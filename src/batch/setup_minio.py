"""Setup MinIO bucket for raw matches."""
import os
from minio import Minio

MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT','localhost:9000')
MINIO_ACCESS = os.getenv('MINIO_ACCESS_KEY','minioadmin')
MINIO_SECRET = os.getenv('MINIO_SECRET_KEY','minioadmin')
BUCKET = 'raw-matches'

def setup():
    client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS, secret_key=MINIO_SECRET, secure=False)
    if not client.bucket_exists(BUCKET):
        client.make_bucket(BUCKET)
        print(f'Created bucket {BUCKET}')
    else:
        print(f'Bucket {BUCKET} already exists')

if __name__ == '__main__':
    setup()
