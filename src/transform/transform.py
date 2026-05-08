"""Transform articles_raw into silver and analytical gold tables."""
import json
import os
import re
from collections import Counter

import pandas as pd
from sqlalchemy import create_engine

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


STOPWORDS = {
    'the', 'and', 'for', 'with', 'that', 'this', 'from', 'have', 'has', 'was', 'were', 'are', 'but', 'not',
    'les', 'des', 'une', 'dans', 'sur', 'pour', 'pas', 'avec', 'plus', 'aux', 'par', 'qui', 'que', 'comme',
    'و', 'في', 'على', 'من', 'عن', 'الى', 'إلى', 'مع', 'هذا', 'هذه', 'ذلك', 'تلك'
}


def clean_text(value):
    if not isinstance(value, str):
        return ''
    return re.sub(r'\s+', ' ', value).strip()


def tokenize(value):
    if not isinstance(value, str):
        return []
    tokens = re.findall(r"[\w\u0600-\u06FFÀ-ÿ']{3,}", value.lower())
    return [token for token in tokens if token not in STOPWORDS]


def ensure_silver_columns(df):
    df = df.copy()
    df['published_at'] = pd.to_datetime(df['published_at'], utc=True, errors='coerce')
    df['scraped_at'] = pd.to_datetime(df['fetched_at'], utc=True, errors='coerce')
    df['raw_json'] = df['raw_json'].apply(
        lambda value: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
    )
    df['title_clean'] = df['title'].fillna('').map(clean_text)
    df['content_clean'] = df['content'].fillna('').map(clean_text)
    df['word_count'] = df['content_clean'].map(lambda x: len(tokenize(x)))
    df['char_count'] = df['content_clean'].map(len)
    df['reading_minutes'] = df['word_count'].map(lambda n: max(1, round(n / 200, 2)))
    df['published_day'] = df['published_at'].dt.date
    return df


def write_frame(frame, table_name, eng):
    frame.to_sql(table_name, eng, if_exists='replace', index=False, method='multi', chunksize=500)


def to_silver():
    eng = engine()
    df = pd.read_sql('SELECT * FROM articles_raw', eng)
    if df.empty:
        print('No raw data')
        return
    silver = ensure_silver_columns(df)
    columns = [
        'article_id', 'source', 'source_name', 'source_home', 'title', 'title_clean', 'author',
        'published_at', 'published_day', 'category', 'content', 'content_clean', 'url',
        'fetched_at', 'scraped_at', 'language', 'word_count', 'char_count', 'reading_minutes', 'raw_json'
    ]
    write_frame(silver[columns], 'articles_silver', eng)
    print('Silver written')


def build_keyword_table(silver):
    counter = Counter()
    for _, row in silver.iterrows():
        counter.update(tokenize(f"{row.get('title_clean', '')} {row.get('content_clean', '')}"))
    keywords = pd.DataFrame(counter.most_common(100), columns=['keyword', 'frequency'])
    if keywords.empty:
        keywords = pd.DataFrame(columns=['keyword', 'frequency'])
    return keywords

def to_gold():
    eng = engine()
    df = pd.read_sql('SELECT * FROM articles_silver', eng)
    if df.empty:
        print('No silver data')
        return
    silver = df.copy()
    silver['published_at'] = pd.to_datetime(silver['published_at'], utc=True, errors='coerce')
    silver['published_day'] = pd.to_datetime(silver['published_day'], errors='coerce').dt.date

    trends = (
        silver.groupby('published_day', dropna=False)
        .agg(
            articles_count=('article_id', 'nunique'),
            avg_word_count=('word_count', 'mean'),
            avg_reading_minutes=('reading_minutes', 'mean'),
            unique_sources=('source', 'nunique'),
        )
        .reset_index()
        .sort_values('published_day')
    )
    sources = (
        silver.groupby('source', dropna=False)
        .agg(articles_count=('article_id', 'nunique'))
        .reset_index()
        .sort_values('articles_count', ascending=False)
    )
    categories = (
        silver.groupby('category', dropna=False)
        .agg(articles_count=('article_id', 'nunique'))
        .reset_index()
        .sort_values('articles_count', ascending=False)
    )
    keywords = build_keyword_table(silver)

    write_frame(trends, 'articles_gold_trends', eng)
    write_frame(sources, 'articles_gold_sources', eng)
    write_frame(categories, 'articles_gold_categories', eng)
    write_frame(keywords, 'articles_gold_keywords', eng)
    print('Gold written')

if __name__ == '__main__':
    to_silver(); to_gold()
