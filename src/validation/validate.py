"""Data quality checks for the article pipeline."""
import os

from sqlalchemy import create_engine, text

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

def run_checks():
    eng = engine()
    with eng.connect() as conn:
        total_raw = conn.execute(text('SELECT COUNT(*) FROM articles_raw')).scalar()
        total_silver = conn.execute(text('SELECT COUNT(*) FROM articles_silver')).scalar()
        duplicate_urls = conn.execute(text('SELECT COUNT(*) - COUNT(DISTINCT url) FROM articles_raw')).scalar()
        missing_titles = conn.execute(text("SELECT COUNT(*) FROM articles_raw WHERE title IS NULL OR title = ''")).scalar()
        missing_content = conn.execute(text("SELECT COUNT(*) FROM articles_raw WHERE content IS NULL OR content = ''")).scalar()
        print('Total raw rows:', total_raw)
        print('Total silver rows:', total_silver)
        print('Duplicate URLs:', duplicate_urls)
        print('Missing titles:', missing_titles)
        print('Missing content:', missing_content)

if __name__ == '__main__':
    run_checks()
