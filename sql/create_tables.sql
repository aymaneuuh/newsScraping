CREATE TABLE IF NOT EXISTS articles_raw (
  article_id TEXT PRIMARY KEY,
  source TEXT,
  source_name TEXT,
  source_home TEXT,
  title TEXT,
  author TEXT,
  published_at TIMESTAMPTZ,
  category TEXT,
  content TEXT,
  url TEXT UNIQUE,
  fetched_at TIMESTAMPTZ,
  language TEXT,
  raw_json JSONB
);

CREATE TABLE IF NOT EXISTS articles_silver (
  article_id TEXT PRIMARY KEY,
  source TEXT,
  source_name TEXT,
  source_home TEXT,
  title TEXT,
  title_clean TEXT,
  author TEXT,
  published_at TIMESTAMPTZ,
  published_day DATE,
  category TEXT,
  content TEXT,
  content_clean TEXT,
  url TEXT UNIQUE,
  fetched_at TIMESTAMPTZ,
  scraped_at TIMESTAMPTZ,
  language TEXT,
  word_count INT,
  char_count INT,
  reading_minutes NUMERIC,
  raw_json JSONB
);

CREATE TABLE IF NOT EXISTS articles_gold_trends (
  published_day DATE PRIMARY KEY,
  articles_count INT,
  avg_word_count NUMERIC,
  avg_reading_minutes NUMERIC,
  unique_sources INT
);

CREATE TABLE IF NOT EXISTS articles_gold_sources (
  source TEXT PRIMARY KEY,
  articles_count INT
);

CREATE TABLE IF NOT EXISTS articles_gold_categories (
  category TEXT PRIMARY KEY,
  articles_count INT
);

CREATE TABLE IF NOT EXISTS articles_gold_keywords (
  keyword TEXT PRIMARY KEY,
  frequency INT
);
