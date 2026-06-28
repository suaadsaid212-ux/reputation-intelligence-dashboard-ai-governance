import streamlit as st
import pandas as pd
import feedparser
import plotly.graph_objects as go
import matplotlib.pyplot as plt

from wordcloud import WordCloud
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from urllib.parse import quote_plus

st.set_page_config(
    page_title="Narrative Intelligence",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 Narrative Intelligence")

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
    "Country",
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
def get_narratives(entity_name, short_name, query):
    encoded_query = quote_plus(query)

    feed = feedparser.parse(
        f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    )

    rows = []

    for entry in feed.entries[:25]:
        title = entry.title
        score = analyzer.polarity_scores(title)["compound"]

        if score >= 0.3:
            label = "Positive"
        elif score <= -0.3:
            label = "Negative"
        else:
            label = "Neutral"

        if score <= -0.5:
            risk_label = "High Risk Narrative"
        elif score <= -0.2:
            risk_label = "Moderate Risk Narrative"
        else:
            risk_label = "Low Risk Narrative"

        rows.append({
            "Entity": entity_name,
            "Short Name": short_name,
            "Headline": title,
            "Sentiment": round(float(score), 3),
            "Sentiment Label": label,
            "Narrative Risk": risk_label,
        })

    return rows


rows = []

for _, entity in selected_df.iterrows():
    rows.extend(
        get_narratives(
            entity["Entity_Name"],
            entity["Short_Name"],
            entity["News_Query"],
        )
    )

narrative_df = pd.DataFrame(rows)

if narrative_df.empty:
    st.error("No narrative data available.")
    st.stop()

st.subheader("Narrative Feed")

st.dataframe(
    narrative_df,
    use_container_width=True,
    hide_index=True,
)

st.subheader("High-Risk Narratives")

high_risk_df = narrative_df[
    narrative_df["Narrative Risk"] != "Low Risk Narrative"
]

if high_risk_df.empty:
    st.info("No high-risk narratives detected.")
else:
    st.dataframe(
        high_risk_df.sort_values(
            by="Sentiment",
        ),
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Narrative Sentiment Distribution")

sentiment_counts = (
    narrative_df["Sentiment Label"]
    .value_counts()
)

pie_fig = go.Figure(
    data=[
        go.Pie(
            labels=sentiment_counts.index,
            values=sentiment_counts.values,
            hole=0.45,
        )
    ]
)

pie_fig.update_layout(
    height=500,
)

st.plotly_chart(
    pie_fig,
    use_container_width=True,
)

st.subheader("Narrative Risk Distribution")

risk_counts = (
    narrative_df["Narrative Risk"]
    .value_counts()
)

risk_fig = go.Figure()

risk_fig.add_trace(
    go.Bar(
        x=risk_counts.index,
        y=risk_counts.values,
        text=risk_counts.values,
        textposition="auto",
    )
)

risk_fig.update_layout(
    height=500,
)

st.plotly_chart(
    risk_fig,
    use_container_width=True,
)

st.subheader("Organization Narrative Word Clouds")

for short_name in narrative_df["Short Name"].unique():
    company_df = narrative_df[
        narrative_df["Short Name"] == short_name
    ]

    text = " ".join(
        company_df["Headline"].tolist()
    )

    if text.strip() == "":
        continue

    wordcloud = WordCloud(
        width=1200,
        height=600,
        background_color="white",
        colormap="Reds",
    ).generate(text)

    fig, ax = plt.subplots(
        figsize=(14, 7),
    )

    ax.imshow(
        wordcloud,
        interpolation="bilinear",
    )

    ax.axis("off")

    ax.set_title(
        f"{short_name} Narrative Keywords",
        fontsize=20,
    )

    st.pyplot(fig)

st.subheader("Most Negative Narratives by Organization")

for short_name in narrative_df["Short Name"].unique():
    company_df = narrative_df[
        narrative_df["Short Name"] == short_name
    ]

    company_negative = company_df.sort_values(
        by="Sentiment",
    ).head(5)

    st.write(f"### {short_name}")

    st.dataframe(
        company_negative,
        use_container_width=True,
        hide_index=True,
    )
