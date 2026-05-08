from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

DEFAULT_ARGS = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

COMMON_ENV = {
    'POSTGRES_HOST': 'postgres',
    'POSTGRES_PORT': '5432',
    'POSTGRES_DB': 'football_dw',
    'POSTGRES_USER': 'pguser',
    'POSTGRES_PASSWORD': 'pgpassword',
    'MINIO_ENDPOINT': 'minio:9000',
    'MINIO_ACCESS_KEY': 'minioadmin',
    'MINIO_SECRET_KEY': 'minioadmin',
    'KAFKA_BOOTSTRAP_SERVERS': 'kafka:9092',
    'KAFKA_TOPIC': 'news_articles',
    'KAFKA_GROUP_ID': 'airflow-stream-processor',
    'KAFKA_OFFSET_RESET': 'earliest',
    'BRONZE_BUCKET': 'bronze-articles',
    'BRONZE_PREFIX': 'bronze/news',
    'NEWS_SOURCES': 'bbc,hespress,france24',
    'SCRAPER_MAX_ARTICLES_PER_SOURCE': '6',
    'MAX_MESSAGES': '24',
}

with DAG(
    dag_id='news_media_pipeline',
    default_args=DEFAULT_ARGS,
    description='Scrape news articles, stream them to Kafka, store Bronze in MinIO, and build Silver/Gold tables',
    schedule_interval='@hourly',
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:

    create_tables = BashOperator(
        task_id='create_tables',
        bash_command='python /opt/airflow/src/warehouse/load_dw.py',
        env=COMMON_ENV,
    )

    run_scraper = BashOperator(
        task_id='run_scraper',
        bash_command='python /opt/airflow/src/collector/producer.py',
        env=COMMON_ENV,
    )

    consume_bronze = BashOperator(
        task_id='consume_bronze',
        bash_command='python /opt/airflow/src/consumer/stream_processor.py',
        env=COMMON_ENV,
    )

    ingest = BashOperator(
        task_id='ingest_to_dw',
        bash_command='python /opt/airflow/src/batch/ingest_batch.py',
        env=COMMON_ENV,
    )

    transform = BashOperator(
        task_id='transform_medallion',
        bash_command='python /opt/airflow/src/transform/transform.py',
        env=COMMON_ENV,
    )

    validate = BashOperator(
        task_id='validate_data',
        bash_command='python /opt/airflow/src/validation/validate.py',
        env=COMMON_ENV,
    )

    create_tables >> run_scraper >> consume_bronze >> ingest >> transform >> validate
