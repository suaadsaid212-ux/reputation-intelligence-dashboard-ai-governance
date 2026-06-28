import streamlit as st
import pandas as pd
import feedparser
import plotly.graph_objects as go

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
from urllib.parse import quote_plus
from utils.glossary import render_glossary

st.set_page_config(
    page_title="Sentiment & Subjectivity",
    page_icon="💬",
    layout="wide",
)

st.title("💬 Sentiment & Subjectivity Intelligence")

render_glossary(["VADER"])

try:
    registry_df = pd.read_csv(
        "config/entity_registry.csv",
        encoding="utf-8-sig",
    )
except FileNotFoundError:
    st.error("Registry file not found: config/entity_registry.csv")
    st.stop()

required_columns = [
    "Entity_Name",
    "Short_Name",
    "Sector",
    "Priority",
    "News_Query",
]

missing_columns = [
    column
    for column in required_columns
    if column not in registry_df.columns
]

if missing_columns:
    st.error(
        "Registry file is missing required columns: "
        + ", ".join(missing_columns)
    )
    st.stop()

sector_filter = st.sidebar.multiselect(
    "Filter by Sector",
    sorted(
        registry_df["Sector"]
        .dropna()
        .unique()
        .tolist()
    ),
)

priority_filter = st.sidebar.multiselect(
    "Filter by Priority",
    sorted(
        registry_df["Priority"]
        .dropna()
        .unique()
        .tolist()
    ),
)

filtered_registry = registry_df.copy()

if sector_filter:
    filtered_registry = filtered_registry[
        filtered_registry["Sector"].isin(sector_filter)
    ]

if priority_filter:
    filtered_registry = filtered_registry[
        filtered_registry["Priority"].isin(priority_filter)
    ]

selected_entities = st.sidebar.multiselect(
    "Select Organizations",
    filtered_registry["Entity_Name"].tolist(),
    default=filtered_registry["Entity_Name"].head(5).tolist(),
)

if not selected_entities:
    st.warning("Select at least one organization.")
    st.stop()

selected_df = filtered_registry[
    filtered_registry["Entity_Name"].isin(selected_entities)
]

analyzer = SentimentIntensityAnalyzer()


@st.cache_data(ttl=1800)
def get_sentiment_rows(entity_name, short_name, query):
    encoded_query = quote_plus(query)

    feed = feedparser.parse(
        f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    )

    rows = []

    for entry in feed.entries[:25]:
        headline = entry.title

        vader_score = analyzer.polarity_scores(
            headline
        )["compound"]

        blob = TextBlob(headline)

        rows.append({
            "Entity": entity_name,
            "Short Name": short_name,
            "Headline": headline,
            "VADER Polarity": round(float(vader_score), 3),
            "TextBlob Polarity": round(float(blob.sentiment.polarity), 3),
            "Subjectivity": round(float(blob.sentiment.subjectivity), 3),
        })

    return rows


rows = []

for _, entity in selected_df.iterrows():
    rows.extend(
        get_sentiment_rows(
            entity["Entity_Name"],
            entity["Short_Name"],
            entity["News_Query"],
        )
    )

df = pd.DataFrame(rows)

if df.empty:
    st.error("No sentiment data available.")
    st.stop()

st.subheader("Sentiment and Subjectivity Dataset")

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
)

summary_df = (
    df.groupby("Short Name")
    .agg({
        "VADER Polarity": "mean",
        "TextBlob Polarity": "mean",
        "Subjectivity": "mean",
    })
    .reset_index()
)

summary_df["VADER Polarity"] = summary_df["VADER Polarity"].round(3)
summary_df["TextBlob Polarity"] = summary_df["TextBlob Polarity"].round(3)
summary_df["Subjectivity"] = summary_df["Subjectivity"].round(3)

st.subheader("Organization-Level Sentiment and Subjectivity Summary")

st.dataframe(
    summary_df,
    use_container_width=True,
    hide_index=True,
)

st.subheader("Average Subjectivity by Organization")

subjectivity_fig = go.Figure()

subjectivity_fig.add_trace(
    go.Bar(
        x=summary_df["Short Name"],
        y=summary_df["Subjectivity"],
        text=summary_df["Subjectivity"],
        textposition="auto",
    )
)

subjectivity_fig.update_layout(
    height=500,
    yaxis_title="Average Subjectivity",
)

st.plotly_chart(
    subjectivity_fig,
    use_container_width=True,
)

st.subheader("Polarity vs Subjectivity Map")

scatter_fig = go.Figure()

for short_name in df["Short Name"].unique():
    entity_df = df[
        df["Short Name"] == short_name
    ]

    scatter_fig.add_trace(
        go.Scatter(
            x=entity_df["VADER Polarity"],
            y=entity_df["Subjectivity"],
            mode="markers",
            name=short_name,
            text=entity_df["Headline"],
            hovertemplate=(
                "<b>%{text}</b><br>"
                + "Polarity: %{x}<br>"
                + "Subjectivity: %{y}<extra></extra>"
            ),
        )
    )

scatter_fig.update_layout(
    xaxis_title="Polarity",
    yaxis_title="Subjectivity",
    height=600,
)

st.plotly_chart(
    scatter_fig,
    use_container_width=True,
)

st.subheader("High Subjectivity Narratives")

high_subjectivity_df = df[
    df["Subjectivity"] >= 0.6
]

if high_subjectivity_df.empty:
    st.info("No highly subjective narratives detected.")
else:
    st.dataframe(
        high_subjectivity_df.sort_values(
            by="Subjectivity",
            ascending=False,
        ),
        use_container_width=True,
        hide_index=True,
    )
