# Projet Big Data Modèle

Ce document sert de base pour recréer un projet du même type que celui d’origine, mais sur un autre sujet.

## 1. Sujet du projet

- Sujet principal : Plateforme Big Data d’analyse de matchs de football et de performances des équipes


Objectif métier : Collecter, traiter et analyser des données de football afin de suivre les performances des équipes et joueurs, détecter des tendances, produire des statistiques avancées et visualiser les résultats en temps réel via des dashboards interactifs.


Public cible :


analystes sportifs,


journalistes sportifs,


supporters et passionnés de football,


clubs ou académies souhaitant exploiter les données de performance.




Sources de données :


APIs football (ex. : API-Football, football-data.org),


scraping de statistiques sportives,


fichiers CSV historiques de matchs,


flux temps réel simulés via Kafka (scores, événements de match, buts, cartons, possession, tirs, etc.).




## 2. Objectif général

Construire une plateforme data complète avec ingestion, transformation, stockage, orchestration et visualisation.

Le projet doit permettre de :

- collecter automatiquement des données depuis plusieurs sources ;
- nettoyer et standardiser ces données ;
- stocker les données brutes et transformées ;
- produire des agrégations utiles pour l’analyse ;
- exposer un tableau de bord interactif ;
- automatiser les traitements avec un orchestrateur.

## 3. Architecture cible

- Collecte / scraping : Python, APIs, BeautifulSoup, requests
- Streaming : Kafka
- Data Lake : MinIO ou stockage compatible S3
- Transformation : Python, Pandas, DuckDB ou SQL
- Orchestration : Airflow
- Data Warehouse : PostgreSQL
- Visualisation : Streamlit et Plotly

## 4. Structure du projet

```text
.
├── docker-compose.yml
├── README.md
├── dags/
├── dashboard/
├── data/
│   ├── raw/
│   ├── processed/
│   ├── silver/
│   └── gold/
├── ingestion/
│   ├── batch_ingestion.py
│   ├── data_quality.py
│   ├── dw_loader.py
│   ├── kafka_consumer.py
│   ├── kafka_producer.py
│   ├── minio_uploader.py
│   └── medallion/
├── logs/
├── logs_airflow/
└── scraping/
``` 

## 5. Pipeline attendu

1. Récupérer les données depuis les sources définies.
2. Stocker une copie brute dans `data/raw`.
3. Alimenter un flux si nécessaire via Kafka.
4. Nettoyer et normaliser les données dans la couche silver.
5. Produire les indicateurs métier dans la couche gold.
6. Charger les résultats dans PostgreSQL.
7. Vérifier la qualité des données.
8. Afficher les résultats dans un dashboard Streamlit.
9. Automatiser le tout avec Airflow.

## 6. Fonctionnalités à prévoir

- tableau de bord avec plusieurs vues ;
- filtres par catégorie, période ou statut ;
- indicateurs clés sous forme de KPI ;
- graphiques de tendance, répartition et comparaison ;
- tableau détaillé des données ;
- historique des traitements ;
- logs et suivi des erreurs.

## 7. Exigences techniques

- code modulaire et lisible ;
- fichier `README.md` clair avec lancement rapide ;
- `docker-compose.yml` pour lancer les services ;
- séparation entre ingestion, transformation, orchestration et dashboard ;
- noms de fichiers cohérents avec le sujet choisi ;
- possibilité de lancer le projet en local.

## 8. Exemple de sujets possibles

- météo et climat ;
- sport et statistiques de matchs ;
- immobilier et prix des biens ;
- e-commerce et ventes ;
- transport et trafic ;
- santé publique ;
- énergie et consommation ;
- emploi et marché du travail.

## 9. Livrables attendus

- l’arborescence complète du projet ;
- les scripts Python principaux ;
- le docker-compose ;
- le DAG Airflow ;
- le dashboard Streamlit ;
- le README d’installation et d’utilisation.

