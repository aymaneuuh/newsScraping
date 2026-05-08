"""Test MinIO access and list objects."""
from minio import Minio

MINIO_ENDPOINT = 'minio:9000'
MINIO_ACCESS = 'minioadmin'
MINIO_SECRET = 'minioadmin'
BUCKET = 'raw-matches'

def test():
    try:
        client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS, secret_key=MINIO_SECRET, secure=False)
        print(f'Connected to MinIO at {MINIO_ENDPOINT}')
        
        if client.bucket_exists(BUCKET):
            print(f'Bucket {BUCKET} exists')
            objects = list(client.list_objects(BUCKET))
            print(f'Found {len(objects)} objects')
            for obj in objects[:10]:
                print(f'  - {obj.object_name} ({obj.size} bytes)')
        else:
            print(f'Bucket {BUCKET} does NOT exist')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    test()
