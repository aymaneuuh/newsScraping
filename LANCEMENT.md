# Guide de lancement — Plateforme Big Data presse

## 1. Démarrage
```bash
docker-compose up -d --build
```

## 2. Contrôles rapides
- Airflow: http://localhost:8081
- Streamlit: http://localhost:8501
- MinIO: http://localhost:9000

## 3. Vérifier les conteneurs
```bash
docker-compose ps
```

## 4. Déclencher le pipeline Airflow
Dans l’UI Airflow, lancer le DAG `news_media_pipeline`.

## 5. Vérifier les données
```bash
docker-compose exec postgres psql -U pguser -d football_dw -c "SELECT COUNT(*) FROM articles_raw;"
docker-compose exec postgres psql -U pguser -d football_dw -c "SELECT COUNT(*) FROM articles_silver;"
docker-compose exec postgres psql -U pguser -d football_dw -c "SELECT COUNT(*) FROM articles_gold_trends;"
```

## 6. Commandes utiles
### Scraper les articles puis publier dans Kafka
```bash
docker-compose exec scraper python /app/src/collector/producer.py
```

### Consommer le flux et écrire le Bronze dans MinIO
```bash
docker-compose exec consumer python /app/src/consumer/stream_processor.py
```

### Charger Bronze -> PostgreSQL
```bash
docker-compose exec pipeline python /app/src/batch/ingest_batch.py
```

### Transformer Silver/Gold
```bash
docker-compose exec pipeline python /app/src/transform/transform.py
```

### Validation qualité
```bash
docker-compose exec pipeline python /app/src/validation/validate.py
```

## 7. Schéma cible
- Bronze: `bronze-articles` dans MinIO
- Raw: `articles_raw`
- Silver: `articles_silver`
- Gold: `articles_gold_trends`, `articles_gold_sources`, `articles_gold_categories`, `articles_gold_keywords`
