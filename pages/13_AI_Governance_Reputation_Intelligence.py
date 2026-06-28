import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.ai_governance_utils import (
    CATEGORY_KEYWORDS,
    LANGUAGE_PROFILES,
    collect_ai_governance_narratives,
)
from utils.entity_selector import get_entity, get_entity_query
from utils.glossary import metric_help, render_glossary


st.set_page_config(
    page_title="AI Governance Reputation Intelligence",
    layout="wide",
)

entity = get_entity()

entity_name = entity["Entity_Name"]
display_name = entity["Short_Name"]
entity_query = get_entity_query(entity, "News_Query")

st.title("AI Governance & Reputation Intelligence")
st.caption(
    "Research prototype module for filtering organisational reputation narratives "
    "to AI governance, digital responsibility, stakeholder trust, and geographic exposure."
)

render_glossary(["AI-GRS", "VADER", "RII", "DSS", "NPI"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Entity", display_name)
c2.metric("Type", entity["Entity_Type"])
c3.metric("Country", entity["Country"])
c4.metric("Sector", entity["Sector"])

st.divider()

category_options = list(CATEGORY_KEYWORDS.keys())
language_label_to_code = {
    profile["label"]: code
    for code, profile in LANGUAGE_PROFILES.items()
    if profile.get("country")
}

default_language_labels = [
    LANGUAGE_PROFILES[code]["label"]
    for code in ["en_gb", "en_us", "ar_om", "ar_ae", "it_it"]
    if code in LANGUAGE_PROFILES
]

selected_categories = st.sidebar.multiselect(
    "AI governance categories",
    category_options,
    default=category_options,
)

limit_per_category = st.sidebar.slider(
    "Headlines per category",
    min_value=5,
    max_value=30,
    value=5,
    step=5,
)

selected_language_labels = st.sidebar.multiselect(
    "Narrative language and country editions",
    sorted(language_label_to_code.keys()),
    default=default_language_labels,
)

strict_matching = st.sidebar.checkbox(
    "Require AI-governance keyword match",
    value=True,
)

entity_aliases_input = st.sidebar.text_input(
    "Entity aliases for multilingual search",
    "",
    help=(
        "Optional comma-separated local names, such as Arabic, Russian, Chinese, "
        "Japanese, or Hindi versions of the selected organisation."
    ),
)

custom_terms_input = st.sidebar.text_input(
    "Additional research terms",
    "",
)

custom_terms = [
    term.strip().lower()
    for term in custom_terms_input.split(",")
    if term.strip()
]

entity_aliases = [
    alias.strip()
    for alias in entity_aliases_input.split(",")
    if alias.strip()
]

language_codes = [
    language_label_to_code[label]
    for label in selected_language_labels
]

if not selected_categories:
    st.warning("Select at least one AI governance category.")
    st.stop()

if not language_codes:
    st.warning("Select at least one narrative language/country edition.")
    st.stop()

with st.spinner("Collecting multilingual AI-governance-related narratives..."):
    rows = collect_ai_governance_narratives(
        entity_name=entity_name,
        short_name=display_name,
        entity_query=entity_query,
        selected_categories=selected_categories,
        limit_per_category=limit_per_category,
        strict_matching=strict_matching,
        custom_terms=custom_terms,
        language_codes=language_codes,
        entity_aliases=entity_aliases,
    )

df = pd.DataFrame(rows)

if df.empty:
    st.warning(
        "No AI-governance-related narratives were detected for the current "
        "entity, language editions, and category settings."
    )
    st.info(
        "Try reducing strict matching, selecting fewer categories, adding local "
        "entity aliases, or adding research terms such as Copilot, OpenAI, privacy, "
        "automation, or data governance."
    )
    st.stop()

avg_risk = round(float(df["Governance Risk Score"].mean()), 2)
avg_sentiment = round(float(df["Sentiment"].mean()), 3)
high_risk_count = int((df["Governance Risk Score"] >= 60).sum())
country_count = int(df["Edition Country"].nunique())

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric(
    "AI-Governance Narratives",
    len(df),
    help="Filtered public narratives matching the selected AI governance taxonomy.",
)
k2.metric("Avg AI-GRS", avg_risk, help=metric_help("AI-GRS"))
k3.metric(
    "Avg Sentiment",
    avg_sentiment,
    help="Average sentiment polarity across selected editions. Non-English values use prototype lexicons.",
)
k4.metric(
    "Country Editions",
    country_count,
    help="Number of Google News country editions returning matched narratives.",
)
k5.metric(
    "High-Risk Narratives",
    high_risk_count,
    help="Narratives with an AI Governance Risk Score of 60 or above.",
)

if avg_risk >= 60:
    st.error("Elevated AI-governance reputation pressure detected.")
elif avg_risk >= 35:
    st.warning("Moderate AI-governance reputation pressure detected.")
else:
    st.success("Low AI-governance reputation pressure detected.")

st.info(
    "Multilingual collection uses Google News language/country editions and "
    "language-specific keyword taxonomies. Geography reflects the selected news "
    "edition, not the exact reader location. English sentiment uses VADER/TextBlob; "
    "other languages use a prototype lexicon that should be validated during the fellowship."
)

st.subheader("Geographic Narrative Exposure")

geo_summary = (
    df.groupby([
        "Edition Country",
        "Edition Region",
        "Edition ISO3",
        "Edition Latitude",
        "Edition Longitude",
    ])
    .agg({
        "Headline": "count",
        "Governance Risk Score": "mean",
        "Sentiment": "mean",
    })
    .rename(columns={"Headline": "Narrative Count"})
    .reset_index()
)

geo_summary["Governance Risk Score"] = geo_summary["Governance Risk Score"].round(2)
geo_summary["Sentiment"] = geo_summary["Sentiment"].round(3)
geo_summary["Marker Size"] = geo_summary["Narrative Count"].clip(lower=1) * 6 + 10

geo_left, geo_right = st.columns(2)

with geo_left:
    map_fig = go.Figure()
    map_fig.add_trace(
        go.Scattergeo(
            lon=geo_summary["Edition Longitude"],
            lat=geo_summary["Edition Latitude"],
            text=(
                geo_summary["Edition Country"]
                + "<br>Narratives: "
                + geo_summary["Narrative Count"].astype(str)
                + "<br>Avg AI-GRS: "
                + geo_summary["Governance Risk Score"].astype(str)
                + "<br>Avg sentiment: "
                + geo_summary["Sentiment"].astype(str)
            ),
            mode="markers",
            marker={
                "size": geo_summary["Marker Size"],
                "color": geo_summary["Governance Risk Score"],
                "colorscale": "Reds",
                "showscale": True,
                "colorbar": {"title": "AI-GRS"},
                "line": {"width": 0.5, "color": "white"},
            },
            hovertemplate="%{text}<extra></extra>",
        )
    )
    map_fig.update_layout(
        height=520,
        geo={
            "showland": True,
            "landcolor": "rgb(245, 245, 245)",
            "countrycolor": "rgb(220, 220, 220)",
            "showcountries": True,
        },
        margin={"l": 0, "r": 0, "t": 10, "b": 0},
    )
    st.plotly_chart(map_fig, use_container_width=True)

with geo_right:
    country_fig = go.Figure()
    country_fig.add_trace(
        go.Bar(
            x=geo_summary["Edition Country"],
            y=geo_summary["Sentiment"],
            text=geo_summary["Sentiment"],
            textposition="auto",
            marker={
                "color": geo_summary["Governance Risk Score"],
                "colorscale": "Reds",
            },
        )
    )
    country_fig.update_layout(
        height=520,
        xaxis_title="News edition country",
        yaxis_title="Average sentiment",
        yaxis_range=[-1, 1],
    )
    st.plotly_chart(country_fig, use_container_width=True)

st.dataframe(
    geo_summary[
        [
            "Edition Country",
            "Edition Region",
            "Narrative Count",
            "Sentiment",
            "Governance Risk Score",
        ]
    ].sort_values(by="Governance Risk Score", ascending=False),
    use_container_width=True,
    hide_index=True,
)

st.subheader("Governance Narrative Exposure")

category_summary = (
    df.groupby(["Language", "Edition Country", "Primary Category"])
    .agg({
        "Headline": "count",
        "Governance Risk Score": "mean",
        "Sentiment": "mean",
        "Subjectivity": "mean",
    })
    .rename(columns={"Headline": "Narrative Count"})
    .reset_index()
)

category_summary["Governance Risk Score"] = (
    category_summary["Governance Risk Score"].round(2)
)
category_summary["Sentiment"] = category_summary["Sentiment"].round(3)
category_summary["Subjectivity"] = category_summary["Subjectivity"].round(3)

col_left, col_right = st.columns(2)

with col_left:
    exposure_fig = go.Figure()

    for country in category_summary["Edition Country"].unique():
        country_df = category_summary[category_summary["Edition Country"] == country]
        exposure_fig.add_trace(
            go.Bar(
                x=country_df["Primary Category"],
                y=country_df["Narrative Count"],
                text=country_df["Narrative Count"],
                textposition="auto",
                name=country,
            )
        )

    exposure_fig.update_layout(
        height=520,
        xaxis_title="AI governance category",
        yaxis_title="Narrative count",
        barmode="group",
    )
    st.plotly_chart(exposure_fig, use_container_width=True)

with col_right:
    risk_fig = go.Figure()

    for country in category_summary["Edition Country"].unique():
        country_df = category_summary[category_summary["Edition Country"] == country]
        risk_fig.add_trace(
            go.Bar(
                x=country_df["Primary Category"],
                y=country_df["Governance Risk Score"],
                text=country_df["Governance Risk Score"],
                textposition="auto",
                name=country,
            )
        )

    risk_fig.update_layout(
        height=520,
        xaxis_title="AI governance category",
        yaxis_title="Average governance risk score",
        yaxis_range=[0, 100],
        barmode="group",
    )
    st.plotly_chart(risk_fig, use_container_width=True)

st.subheader("Sentiment, Subjectivity and Governance Risk")

scatter_fig = go.Figure()

for country in df["Edition Country"].unique():
    country_df = df[df["Edition Country"] == country]
    scatter_fig.add_trace(
        go.Scatter(
            x=country_df["Sentiment"],
            y=country_df["Subjectivity"],
            mode="markers",
            name=country,
            marker={
                "size": country_df["Governance Risk Score"].clip(lower=8) / 2,
                "opacity": 0.72,
            },
            text=country_df["Headline"],
            customdata=country_df[["Language", "Primary Category", "Sentiment Method"]],
            hovertemplate=(
                "<b>%{text}</b><br>"
                + "Language: %{customdata[0]}<br>"
                + "Category: %{customdata[1]}<br>"
                + "Method: %{customdata[2]}<br>"
                + "Sentiment: %{x}<br>"
                + "Subjectivity: %{y}<extra></extra>"
            ),
        )
    )

scatter_fig.update_layout(
    height=600,
    xaxis_title="Sentiment polarity",
    yaxis_title="Subjectivity",
)

st.plotly_chart(scatter_fig, use_container_width=True)

st.subheader("AI Governance Narrative Summary")

st.dataframe(
    category_summary.sort_values(
        by=["Edition Country", "Governance Risk Score"],
        ascending=False,
    ),
    use_container_width=True,
    hide_index=True,
)

st.subheader("Risk-Ranked AI Governance Narratives")

display_columns = [
    "Language",
    "Edition Country",
    "Edition Region",
    "Primary Category",
    "Headline",
    "Source",
    "Published",
    "Sentiment Method",
    "Sentiment",
    "Sentiment Label",
    "Subjectivity",
    "Governance Risk Score",
    "Matched Keywords",
    "Risk Terms",
    "Entity Query",
    "Link",
]

st.dataframe(
    df[display_columns]
    .sort_values(by="Governance Risk Score", ascending=False)
    .reset_index(drop=True),
    use_container_width=True,
    hide_index=True,
)

st.subheader("Research Corpus Definition")

with st.expander("AI-governance keyword taxonomy and inclusion rule"):
    st.write(
        "The module creates a focused research corpus by combining the selected "
        "organisation query with AI-governance categories. In strict mode, a "
        "headline or summary must contain at least one governance keyword."
    )

    taxonomy_rows = []

    for category, keywords in CATEGORY_KEYWORDS.items():
        taxonomy_rows.append({
            "Category": category,
            "Core English Keywords": ", ".join(keywords),
        })

    st.dataframe(
        pd.DataFrame(taxonomy_rows),
        use_container_width=True,
        hide_index=True,
    )

with st.expander("Search queries used in this run"):
    query_df = (
        df[[
            "Language",
            "Edition Country",
            "Edition Region",
            "Primary Category",
            "Entity Query",
            "Search Query",
        ]]
        .drop_duplicates()
        .sort_values(by=["Edition Country", "Language", "Primary Category"])
    )
    st.dataframe(
        query_df,
        use_container_width=True,
        hide_index=True,
    )
