"""Batch ingestion: read Bronze JSONL files from MinIO and load them into Postgres (articles_raw)."""
import hashlib
import json
import os
import tempfile
from datetime import datetime

import pandas as pd
from minio import Minio
from psycopg2.extras import Json, execute_values
from sqlalchemy import create_engine, text

MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT','localhost:9000')
MINIO_ACCESS = os.getenv('MINIO_ACCESS_KEY','minioadmin')
MINIO_SECRET = os.getenv('MINIO_SECRET_KEY','minioadmin')
BUCKET = os.getenv('BRONZE_BUCKET', 'bronze-articles')
BRONZE_PREFIX = os.getenv('BRONZE_PREFIX', 'bronze/news')

PG = {
    'host': os.getenv('POSTGRES_HOST','localhost'),
    'port': os.getenv('POSTGRES_PORT','5432'),
    'db': os.getenv('POSTGRES_DB','football_dw'),
    'user': os.getenv('POSTGRES_USER','pguser'),
    'password': os.getenv('POSTGRES_PASSWORD','pgpassword')
}

def engine():
    url = f"postgresql+psycopg2://{PG['user']}:{PG['password']}@{PG['host']}:{PG['port']}/{PG['db']}"
    return create_engine(url)


def parse_datetime(value):
    if not value:
        return None
    try:
        parsed = pd.to_datetime(value, utc=True, errors='coerce')
    except Exception:
        return None
    if pd.isna(parsed):
        return None
    return parsed.to_pydatetime()


def article_identifier(article):
    if article.get('article_id'):
        return article['article_id']
    url = article.get('url', '')
    return hashlib.sha1(url.encode('utf-8')).hexdigest()


def read_jsonl(path):
    rows = []
    with open(path, 'r', encoding='utf-8') as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def main():
    client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS, secret_key=MINIO_SECRET, secure=False)
    objects = client.list_objects(BUCKET, prefix=BRONZE_PREFIX, recursive=True)
    eng = engine()
    inserted = 0
    insert_sql = """
        INSERT INTO articles_raw (
            article_id, source, source_name, source_home, title, author,
            published_at, category, content, url, fetched_at, language, raw_json
        ) VALUES %s
        ON CONFLICT (article_id) DO NOTHING
    """
    for obj in objects:
        name = obj.object_name
        if not name.endswith('.jsonl'):
            continue
        local = os.path.join(tempfile.gettempdir(), name.replace('/', '_'))
        client.fget_object(BUCKET, name, local)
        rows = read_jsonl(local)
        if not rows:
            continue

        values = []
        for article in rows:
            payload = (
                article_identifier(article),
                article.get('source'),
                article.get('source_name'),
                article.get('source_home'),
                article.get('title'),
                article.get('author'),
                parse_datetime(article.get('published_at')),
                article.get('category'),
                article.get('content'),
                article.get('url'),
                parse_datetime(article.get('fetched_at')),
                article.get('language'),
                Json(article),
            )
            values.append(payload)

        with eng.begin() as conn:
            cursor = conn.connection.cursor()
            execute_values(cursor, insert_sql, values, page_size=100)
            cursor.close()
        inserted += len(values)
        print('Ingested', len(values), 'articles from', name)

    print('Total inserted candidates:', inserted)

if __name__ == '__main__':
    main()
