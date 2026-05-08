"""Kafka consumer that writes news articles to MinIO as Bronze JSONL files."""
import os
import json
import time
import tempfile
from datetime import datetime
from kafka import KafkaConsumer
import pandas as pd
from minio import Minio
from minio.error import S3Error

MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT','localhost:9000')
MINIO_ACCESS = os.getenv('MINIO_ACCESS_KEY','minioadmin')
MINIO_SECRET = os.getenv('MINIO_SECRET_KEY','minioadmin')
BUCKET = os.getenv('BRONZE_BUCKET', 'bronze-articles')
BRONZE_PREFIX = os.getenv('BRONZE_PREFIX', 'bronze/news')

KAFKA_BOOTSTRAP = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'news_articles')
KAFKA_GROUP_ID = os.getenv('KAFKA_GROUP_ID', 'stream-processor')
KAFKA_OFFSET_RESET = os.getenv('KAFKA_OFFSET_RESET', 'earliest')
FLUSH_SIZE = int(os.getenv('BRONZE_FLUSH_SIZE', '20'))
FLUSH_SECONDS = int(os.getenv('BRONZE_FLUSH_SECONDS', '15'))
MAX_MESSAGES = int(os.getenv('MAX_MESSAGES', '0'))

def ensure_bucket(client, bucket):
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
    except S3Error as e:
        print('MinIO error', e)


def flush_buffer(client, buffer, sequence):
    if not buffer:
        return sequence
    date_tag = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    fname = f"news_{date_tag}_{sequence}.jsonl"
    local = os.path.join(tempfile.gettempdir(), fname)
    with open(local, 'w', encoding='utf-8') as handle:
        for item in buffer:
            handle.write(json.dumps(item, ensure_ascii=False) + '\n')
    object_name = f"{BRONZE_PREFIX}/{fname}" if BRONZE_PREFIX else fname
    client.fput_object(BUCKET, object_name, local)
    print('Uploaded', object_name)
    return sequence + 1

def main():
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP.split(','),
        auto_offset_reset=KAFKA_OFFSET_RESET,
        enable_auto_commit=True,
        group_id=KAFKA_GROUP_ID,
        api_version=(2, 5, 0)
    )
    client = Minio(MINIO_ENDPOINT,
                   access_key=MINIO_ACCESS,
                   secret_key=MINIO_SECRET,
                   secure=False)
    ensure_bucket(client, BUCKET)

    buffer = []
    sequence = 1
    last_flush = time.time()
    processed = 0
    for msg in consumer:
        try:
            data = json.loads(msg.value.decode('utf-8'))
        except Exception:
            continue
        buffer.append(data)
        processed += 1
        if len(buffer) >= FLUSH_SIZE or time.time() - last_flush > FLUSH_SECONDS:
            sequence = flush_buffer(client, buffer, sequence)
            buffer = []
            last_flush = time.time()
        if MAX_MESSAGES and processed >= MAX_MESSAGES:
            break

    if buffer:
        flush_buffer(client, buffer, sequence)

if __name__ == '__main__':
    main()
