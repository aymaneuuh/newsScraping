"""Simulate scraping / API calls producing match events as JSON lines."""
import json
import random



"""Compatibility wrapper that emits scraped news articles as JSON lines."""
import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.collector.scraper import scrape_news_articles

if __name__ == "__main__":
    for article in scrape_news_articles():
        print(json.dumps(article, ensure_ascii=False))
