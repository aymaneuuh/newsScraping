import os

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine

PG = {
    'host': os.getenv('POSTGRES_HOST','postgres'),
    'port': os.getenv('POSTGRES_PORT','5432'),
    'db': os.getenv('POSTGRES_DB','football_dw'),
    'user': os.getenv('POSTGRES_USER','pguser'),
    'password': os.getenv('POSTGRES_PASSWORD','pgpassword')
}

def engine():
    url = f"postgresql+psycopg2://{PG['user']}:{PG['password']}@{PG['host']}:{PG['port']}/{PG['db']}"
    return create_engine(url)

st.set_page_config(page_title='Tendances médiatiques', layout='wide')
st.title('Dashboard — Analyse d\'articles de presse et de tendances médiatiques')

eng = engine()

def query_table(sql):
    try:
        return pd.read_sql(sql, eng)
    except Exception:
        return pd.DataFrame()

silver = query_table('SELECT * FROM articles_silver ORDER BY published_at DESC')
trends = query_table('SELECT * FROM articles_gold_trends ORDER BY published_day')
sources = query_table('SELECT * FROM articles_gold_sources ORDER BY articles_count DESC')
categories = query_table('SELECT * FROM articles_gold_categories ORDER BY articles_count DESC')
keywords = query_table('SELECT * FROM articles_gold_keywords ORDER BY frequency DESC')

try:
    df = silver.copy()
except Exception:
    df = pd.DataFrame()

if silver.empty:
    st.warning('Aucune donnée trouvée dans articles_silver. Exécutez le pipeline Docker.')

if not silver.empty:
    st.sidebar.header('Filtres')
    source_options = sorted(silver['source'].dropna().unique().tolist())
    category_options = sorted(silver['category'].dropna().unique().tolist())
    selected_sources = st.sidebar.multiselect('Sources', source_options, default=source_options)
    selected_categories = st.sidebar.multiselect('Catégories', category_options, default=category_options)

    filtered = silver.copy()
    if selected_sources:
        filtered = filtered[filtered['source'].isin(selected_sources)]
    if selected_categories:
        filtered = filtered[filtered['category'].isin(selected_categories)]

    base_df = filtered if not filtered.empty else silver

    st.header('KPI')
    cols = st.columns(4)
    cols[0].metric('Articles', len(base_df))
    cols[1].metric('Sources', base_df['source'].nunique())
    cols[2].metric('Catégories', base_df['category'].nunique())
    cols[3].metric('Mots moyens', round(base_df['word_count'].mean(), 1) if not base_df.empty else 0)

    if base_df is not silver and not base_df.empty:
        trend_view = (
            base_df.assign(published_day=pd.to_datetime(base_df['published_at'], errors='coerce').dt.date)
            .groupby('published_day')
            .size()
            .reset_index(name='articles_count')
        )
        source_view = base_df.groupby('source').size().reset_index(name='articles_count')
        category_view = base_df.groupby('category').size().reset_index(name='articles_count')
        keyword_counter = (
            base_df['content_clean'].fillna('').str.lower().str.extractall(r'([\w\u0600-\u06FFÀ-ÿ]{3,})')[0]
            .value_counts()
            .reset_index()
        )
        keyword_counter.columns = ['keyword', 'frequency']
    else:
        trend_view = trends
        source_view = sources
        category_view = categories
        keyword_counter = keywords

    st.header('Tendances d\'actualité')
    if not trend_view.empty:
        fig = px.line(trend_view, x='published_day', y='articles_count', markers=True)
        st.plotly_chart(fig, use_container_width=True)

    cols = st.columns(2)
    with cols[0]:
        st.subheader('Articles par source')
        if not source_view.empty:
            fig = px.bar(source_view, x='source', y='articles_count', color='source')
            st.plotly_chart(fig, use_container_width=True)
    with cols[1]:
        st.subheader('Top catégories')
        if not category_view.empty:
            fig = px.bar(category_view.head(10), x='category', y='articles_count', color='category')
            st.plotly_chart(fig, use_container_width=True)

    st.header('Mots-clés fréquents')
    if not keyword_counter.empty:
        top_keywords = keyword_counter.head(20)
        fig = px.bar(top_keywords, x='keyword', y='frequency', color='frequency')
        st.plotly_chart(fig, use_container_width=True)

    st.header('Articles récents')
    display_cols = ['published_at', 'source', 'category', 'title', 'author', 'url']
    existing_cols = [col for col in display_cols if col in base_df.columns]
    st.dataframe(base_df[existing_cols].head(100), use_container_width=True)

