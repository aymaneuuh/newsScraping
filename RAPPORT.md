# Rapport technique — Plateforme Big Data d'analyse d'articles de presse

## 1. Resume executif
Ce projet met en place une plateforme Big Data complete pour collecter, traiter et analyser des articles de presse en temps quasi reel. La chaine de traitement couvre le scraping, l'event streaming avec Kafka, le Data Lake (MinIO), la transformation Medaillon (Bronze/Silver/Gold), le Data Warehouse (PostgreSQL), l'orchestration Airflow, la qualite des donnees et un dashboard Streamlit.

Objectif: fournir une base analytique pour l'analyse de tendances mediatiques (sources, categories, mots-cles, evolution temporelle) a partir de sources publiques.

## 2. Contexte et objectifs
- Collecter des articles depuis des sites d'actualite (ex: BBC, France24) avec les attributs: titre, auteur, date de publication, categorie, contenu, source, URL.
- Mettre en place un pipeline de streaming vers Kafka.
- Stocker les donnees brutes dans un Data Lake (Bronze).
- Appliquer des transformations Silver/Gold.
- Charger des tables analytiques dans PostgreSQL.
- Exposer des visualisations dans Streamlit.
- Orchestrer l'ensemble avec Airflow.
- Ajouter des controles qualite et des elements de gouvernance.

## 3. Architecture generale
- Source de donnees: scraping web (BBC, France24).
- Streaming: Kafka (topic `news_articles`).
- Data Lake: MinIO (bucket `bronze-articles`, prefix `bronze/news`).
- Medaillon:
  - Bronze: fichiers JSONL bruts dans MinIO.
  - Silver: table `articles_silver` (nettoyage + enrichissements).
  - Gold: tables d'aggregats `articles_gold_*`.
- Data Warehouse: PostgreSQL (base `football_dw` conservee pour compatibilite).
- Orchestration: Airflow (DAG `news_media_pipeline`).
- Visualisation: Streamlit + Plotly.

## 4. Technologies
- Python 3.x
- Kafka + Zookeeper
- MinIO (S3 compatible)
- PostgreSQL
- Airflow 2.6.x
- Streamlit + Plotly
- Docker Compose

## 5. Structure du projet
```
.
├─ dags/
│  └─ scraper_pipeline_dag.py
├─ src/
│  ├─ collector/ (scraper + producer Kafka)
│  ├─ consumer/ (Kafka -> MinIO Bronze)
│  ├─ batch/ (ingestion Bronze -> Postgres)
│  ├─ transform/ (Silver/Gold)
│  ├─ validation/ (qualite)
│  └─ warehouse/ (creation tables)
├─ sql/
│  ├─ create_tables.sql
│  └─ ddl_medallion.sql
├─ streamlit_app/
│  └─ app.py
├─ docker-compose.yml
├─ requirements.txt
└─ airflow-requirements.txt
```

## 6. Pipeline de donnees (detail)
### 6.1 Scraping
- Fichier: `src/collector/scraper.py`
- Sources actives: BBC, France24.
- France24 est collecte via RSS pour eviter les blocages HTTP (403).
- Extraction des champs: title, author, published_at, category, content, url, source.

### 6.2 Ingestion en streaming (Kafka)
- Producer: `src/collector/producer.py`
- Topic: `news_articles`
- Messages: JSON par article.

### 6.3 Bronze (Data Lake)
- Consumer: `src/consumer/stream_processor.py`
- Stockage: MinIO (JSONL par lot).
- Bucket: `bronze-articles`, prefix `bronze/news`.

### 6.4 Ingestion batch vers DW
- Fichier: `src/batch/ingest_batch.py`
- Lecture MinIO -> insertion Postgres table `articles_raw`.
- Deduplication par `article_id`.

### 6.5 Silver
- Fichier: `src/transform/transform.py`
- Nettoyage: champs normalises, `content_clean`, `title_clean`.
- Enrichissements: `word_count`, `reading_minutes`, `published_day`.
- Table: `articles_silver`.

### 6.6 Gold
- Fichier: `src/transform/transform.py`
- Tables:
  - `articles_gold_trends` (evolution temporelle)
  - `articles_gold_sources` (volume par source)
  - `articles_gold_categories` (volume par categorie)
  - `articles_gold_keywords` (mots-cles frequents)

## 7. Orchestration Airflow
- DAG: `news_media_pipeline`.
- Taches:
  1) `create_tables`
  2) `run_scraper`
  3) `consume_bronze`
  4) `ingest_to_dw`
  5) `transform_medallion`
  6) `validate_data`
Un run complet a ete execute et toutes les taches ont termine en succes.

Run valide (ID): `manual__2026-05-08T18:23:45+00:00`

### Preuves (captures + logs)
Captures a fournir (pour le rapport final):
- Airflow UI avec DAG `news_media_pipeline` en succes.
- Vue Graph/Tree et details de run.
- Dashboard Streamlit avec tableaux et graphiques.

Extraits logs (Airflow):

**run_scraper**
```
INFO:news_scraper:Fetching https://www.bbc.com/news
INFO:news_scraper:Fetching https://www.france24.com/fr/rss
INFO:news_scraper:Scraped 12 articles total
INFO:producer:Sent 12 articles to topic news_articles
```

**consume_bronze**
```
Uploaded bronze/news/news_20260508_182454_1.jsonl
Uploaded bronze/news/news_20260508_182454_2.jsonl
```

**ingest_to_dw**
```
Ingested 12 articles from bronze/news/news_20260508_182444_20.jsonl
Total inserted candidates: 310
```

**transform_medallion**
```
Silver written
Gold written
```

**validate_data**
```
Total raw rows: 16
Total silver rows: 16
Duplicate URLs: 0
Missing titles: 0
Missing content: 0
```

## 8. Qualite et gouvernance des donnees
- Fichier: `src/validation/validate.py`
- Controles:
  - Comptage `articles_raw` vs `articles_silver`
  - Doublons par URL
  - Champs obligatoires manquants (title/content)

### Resultats recents
- Total raw rows: 16
- Total silver rows: 16
- Duplicate URLs: 0
- Missing titles: 0
- Missing content: 0

## 9. Visualisation (Streamlit)
- App: `streamlit_app/app.py`
- Visualisations:
  - Tendances temporelles
  - Articles par source
  - Top categories
  - Mots-cles frequents
  - Tableau des articles recents

### Preuves (captures)
- Capture du dashboard (page KPI + graphiques + table Articles recents)

## 10. Validation end-to-end (resume)
- Scraping: OK (BBC + France24 RSS)
- Kafka: OK (messages produits)
- Bronze: OK (JSONL dans MinIO)
- Ingestion: OK (`articles_raw`)
- Silver/Gold: OK
- Dashboard: OK (data reelles)
- Airflow: OK (run complet succes)
- Qualite: OK (controles valides)

## 11. Limites et axes d'amelioration
- Hespress: source detectee mais non stabilisee (a investiguer).
- Extraction France24: RSS (resume) plutot que contenu complet.
- Ajout d'un module d'authentification/gestion des droits pour la gouvernance.
- Historisation des jeux de donnees et versionning du pipeline.

## 12. Methodologie (academique)
### 12.1 Approche
- Collecte de donnees publiques via scraping web et RSS.
- Modelisation Medaillon: Bronze (brut), Silver (nettoye), Gold (aggregats).
- Separation des flux: streaming pour la collecte, batch pour l'analytique.
- Orchestration centralisee via Airflow pour la reproductibilite.

### 12.2 Design des donnees
- Identifiant article: hash SHA1 de l'URL si `article_id` absent.
- Champs standards: `title`, `author`, `published_at`, `category`, `content`, `url`, `source`.
- Enrichissements Silver: `word_count`, `reading_minutes`, `published_day`.

### 12.3 Evaluation
- Execution de bout en bout via Airflow (run valide).
- Verifications de qualite: doublons, champs manquants, comptages.
- Inspection visuelle: dashboard Streamlit.

## 13. Gouvernance et aspects ethiques
- Donnees publiques uniquement.
- Respect des robots et limites de taux via delais entre requetes.
- Stockage brut trace (Bronze) pour auditabilite.
- Logs d'orchestration pour traçabilite des traitements.

## 14. Guide d'execution (court)
1) `docker-compose up -d --build`
2) Ouvrir Airflow: http://localhost:8081 (admin/admin)
3) Lancer le DAG `news_media_pipeline`
4) Ouvrir Streamlit: http://localhost:8501

## 15. Annexes
- Repo GitHub: https://github.com/aymaneuuh/newsScraping
- Topic Kafka: `news_articles`
- Bucket MinIO: `bronze-articles`
- Prefix Bronze: `bronze/news`
- Tables: `articles_raw`, `articles_silver`, `articles_gold_*`

---

Si tu veux, je peux aussi generer un rapport academique long (methodologie, bibliographie, discussion) a partir de ce fichier.
