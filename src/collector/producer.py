import os
import json
import logging
import time
from typing import Any
from kafka import KafkaProducer
from kafka.errors import KafkaError

from scraper import scrape_news_articles

logger = logging.getLogger("producer")
logging.basicConfig(level=logging.INFO)

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "news_articles")
PRODUCER_RETRIES = int(os.getenv("PRODUCER_RETRIES", "3"))
SCRAPER_LIMIT_PER_SOURCE = int(os.getenv("SCRAPER_MAX_ARTICLES_PER_SOURCE", "6"))
SCRAPER_SOURCES = [s.strip().lower() for s in os.getenv("NEWS_SOURCES", "bbc,hespress").split(",") if s.strip()]


def json_serializer(v: Any) -> bytes:
    return json.dumps(v, default=str).encode('utf-8')


def get_producer() -> KafkaProducer:
    return KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP.split(','), value_serializer=json_serializer,
                         acks='all', retries=5, api_version=(2, 5, 0))


def produce_articles():
    articles = scrape_news_articles(limit_per_source=SCRAPER_LIMIT_PER_SOURCE, sources=SCRAPER_SOURCES)
    if not articles:
        logger.info("No articles fetched")
        return

    producer = get_producer()
    sent = 0
    for article in articles:
        attempts = 0
        while attempts < PRODUCER_RETRIES:
            try:
                key = article.get("article_id") or article.get("url") or ""
                future = producer.send(KAFKA_TOPIC, value=article, key=str(key).encode("utf-8"))
                future.get(timeout=10)
                sent += 1
                break
            except KafkaError as e:
                attempts += 1
                logger.warning("Kafka send failed (attempt %d): %s", attempts, e)
                time.sleep(2 ** attempts)
        else:
            logger.error("Failed to send article after %d tries: %s", PRODUCER_RETRIES, article)
    producer.flush()
    logger.info("Sent %d articles to topic %s", sent, KAFKA_TOPIC)


if __name__ == '__main__':
    try:
        produce_articles()
    except Exception as e:
        logger.exception("Producer failed: %s", e)
