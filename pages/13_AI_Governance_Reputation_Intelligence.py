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
elif high_risk_count > 0:
    st.warning(
        "Overall AI-governance pressure remains low on average, but localized "
        "high-risk narratives require monitoring."
    )
else:
    st.success("Low AI-governance reputation pressure detected.")

st.info(
    "Multilingual collection uses Google News language/country editions and "
    "language-specific keyword taxonomies. Geography reflects the selected news "
    "edition, not the exact reader location. English sentiment uses VADER/TextBlob; "
    "other languages use a prototype lexicon that should be validated during the fellowship."
)
