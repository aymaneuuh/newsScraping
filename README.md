# Projet Big Data — Analyse d’articles de presse et de tendances médiatiques

Plateforme Big Data complète pour scraper des articles d’actualité, les diffuser en streaming via Kafka, les stocker en Bronze dans MinIO, les transformer en Silver/Gold dans PostgreSQL et les visualiser dans Streamlit.

## Stack
- Scraping: Python, `requests`, `BeautifulSoup`
- Streaming: Kafka
- Data Lake: MinIO
- Orchestration: Airflow
- Data Warehouse: PostgreSQL
- Visualisation: Streamlit, Plotly
- Transformation: Pandas, SQL

## Sources
- BBC News
- Hespress

## Pipeline
1. Scraper les articles depuis les sites d’actualité.
2. Envoyer les articles vers Kafka dans le topic `news_articles`.
3. Consommer le flux et déposer les fichiers Bronze JSONL dans MinIO.
4. Charger les données brutes dans PostgreSQL.
5. Produire les couches Silver et Gold.
6. Exposer les tendances dans Streamlit.
7. Orchestrer le tout avec Airflow.

## Lancement Docker
```bash
docker-compose up -d --build
```

## Variables d’environnement
- `API_KEY` si une source externe en a besoin plus tard.
- `NEWS_SOURCES=bbc,hespress`
- `KAFKA_TOPIC=news_articles`
- `BRONZE_BUCKET=bronze-articles`
- `BRONZE_PREFIX=bronze/news`

## Fichiers clés
- [docker-compose.yml](docker-compose.yml)
- [dags/scraper_pipeline_dag.py](dags/scraper_pipeline_dag.py)
- [src/collector/scraper.py](src/collector/scraper.py)
- [src/collector/producer.py](src/collector/producer.py)
- [src/consumer/stream_processor.py](src/consumer/stream_processor.py)
- [src/batch/ingest_batch.py](src/batch/ingest_batch.py)
- [src/transform/transform.py](src/transform/transform.py)
- [streamlit_app/app.py](streamlit_app/app.py)
- [sql/create_tables.sql](sql/create_tables.sql)

## Résultat attendu
- Bronze: articles JSONL dans MinIO
- Silver: articles nettoyés dans PostgreSQL
- Gold: agrégations par jour, source, catégorie et mots-clés
- Dashboard: tendances, sources, catégories, mots-clés fréquents
