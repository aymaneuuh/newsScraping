"""Create article pipeline tables in PostgreSQL."""
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

def create_tables():
    eng = engine()
    sql_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', 'sql', 'create_tables.sql')
    )
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    with eng.begin() as conn:
        conn.execute(text(sql))
    print('Tables created')

if __name__ == '__main__':
    create_tables()
