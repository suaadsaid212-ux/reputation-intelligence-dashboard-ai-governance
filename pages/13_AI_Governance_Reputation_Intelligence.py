import numpy as np
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
    page_title="AI Governance Intelligence Observatory",
    page_icon="🤖",
    layout="wide",
)

entity = get_entity()

entity_name = entity["Entity_Name"]
display_name = entity["Short_Name"]
entity_query = get_entity_query(entity, "News_Query")

st.title("AI Governance Intelligence Observatory")

st.markdown(
    """
    <div class="ti-live">
        <span class="ti-live-dot"></span>
        <span>Live multilingual AI-governance and reputation intelligence</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    f"{display_name} • {entity['Country']} • {entity['Sector']} • "
    "Public narrative monitoring across selected language and country editions"
)

render_glossary(["AI-GRS", "VADER", "RII", "DSS", "NPI"])


# ---------------------------
# Controls
# ---------------------------
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


# ---------------------------
# Data collection
# ---------------------------
with st.spinner(
    "Collecting multilingual AI-governance-related narratives..."
):
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


# ---------------------------
# Core summaries
# ---------------------------
avg_risk = round(
    float(df["Governance Risk Score"].mean()),
    2,
)

avg_sentiment = round(
    float(df["Sentiment"].mean()),
    3,
)

high_risk_count = int(
    (df["Governance Risk Score"] >= 60).sum()
)

country_count = int(
    df["Edition Country"].nunique()
)

language_count = int(
    df["Language"].nunique()
)

category_overall = (
    df.groupby("Primary Category")
    .agg(
        Narrative_Count=("Headline", "count"),
        Avg_Risk=("Governance Risk Score", "mean"),
        Avg_Sentiment=("Sentiment", "mean"),
    )
    .reset_index()
)

category_overall["Avg_Risk"] = (
    category_overall["Avg_Risk"].round(2)
)

category_overall["Avg_Sentiment"] = (
    category_overall["Avg_Sentiment"].round(3)
)

highest_theme_row = (
    category_overall.sort_values(
        "Avg_Risk",
        ascending=False,
    )
    .iloc[0]
)

highest_theme = highest_theme_row["Primary Category"]
highest_theme_risk = float(
    highest_theme_row["Avg_Risk"]
)

country_summary = (
    df.groupby(
        [
            "Edition Country",
            "Edition Region",
            "Edition ISO3",
            "Edition Latitude",
            "Edition Longitude",
        ]
    )
    .agg(
        Narrative_Count=("Headline", "count"),
        Avg_Risk=("Governance Risk Score", "mean"),
        Avg_Sentiment=("Sentiment", "mean"),
    )
    .reset_index()
)

country_summary["Avg_Risk"] = (
    country_summary["Avg_Risk"].round(2)
)

country_summary["Avg_Sentiment"] = (
    country_summary["Avg_Sentiment"].round(3)
)

highest_country_row = (
    country_summary.sort_values(
        "Avg_Risk",
        ascending=False,
    )
    .iloc[0]
)

highest_country = highest_country_row[
    "Edition Country"
]
highest_country_risk = float(
    highest_country_row["Avg_Risk"]
)


# ---------------------------
# Executive KPIs
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Governance status</div>',
    unsafe_allow_html=True,
)

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric(
    "Average AI Governance Risk",
    avg_risk,
    help=metric_help("AI-GRS"),
)

k2.metric(
    "Highest-Risk Theme",
    highest_theme,
)

k3.metric(
    "High-Risk Narratives",
    high_risk_count,
)

k4.metric(
    "Country Editions",
    country_count,
)

k5.metric(
    "Languages Observed",
    language_count,
)


if avg_risk >= 60:
    status_text = "Elevated"
    status_action = (
        "Governance-related reputation pressure is elevated and "
        "requires priority review."
    )
elif avg_risk >= 35:
    status_text = "Monitor"
    status_action = (
        "Governance-related reputation pressure is moderate and "
        "should remain under active monitoring."
    )
else:
    status_text = "Stable"
    status_action = (
        "Governance-related reputation pressure is currently low, "
        "with no broad escalation signal."
    )

brief = (
    f"<strong>{display_name}</strong> has an average AI-governance risk score "
    f"of <strong>{avg_risk:.1f}</strong>, currently classified as "
    f"<strong>{status_text}</strong>. "
    f"The highest-risk governance theme is <strong>{highest_theme}</strong> "
    f"at <strong>{highest_theme_risk:.1f}</strong>. "
    f"The strongest geographic exposure is currently associated with the "
    f"<strong>{highest_country}</strong> news edition at "
    f"<strong>{highest_country_risk:.1f}</strong>. "
    f"{high_risk_count} narrative(s) meet the high-risk threshold. "
    f"{status_action}"
)

st.markdown(
    f"""
    <div class="ti-brief">
        <div class="ti-brief-kicker">Governance Brief</div>
        <div class="ti-brief-text">{brief}</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------
# Theme risk + heatmap
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Governance themes</div>',
    unsafe_allow_html=True,
)
st.subheader("Where is governance pressure concentrated?")

left, right = st.columns([1, 1.2])

with left:
    theme_rank = category_overall.sort_values(
        "Avg_Risk",
        ascending=True,
    )

    theme_fig = go.Figure(
        go.Bar(
            x=theme_rank["Avg_Risk"],
            y=theme_rank["Primary Category"],
            orientation="h",
            text=theme_rank["Avg_Risk"],
            textposition="outside",
            customdata=np.stack(
                [
                    theme_rank["Narrative_Count"],
                    theme_rank["Avg_Sentiment"],
                ],
                axis=-1,
            ),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Average AI-GRS: %{x:.1f}<br>"
                "Narratives: %{customdata[0]}<br>"
                "Average Sentiment: %{customdata[1]:.3f}"
                "<extra></extra>"
            ),
        )
    )

    theme_fig.update_layout(
        height=max(
            390,
            54 * len(theme_rank),
        ),
        margin=dict(
            l=10,
            r=50,
            t=10,
            b=25,
        ),
        xaxis=dict(
            title="Average AI Governance Risk",
            range=[0, 100],
            showgrid=True,
            gridcolor="rgba(100,120,140,.12)",
            zeroline=False,
        ),
        yaxis=dict(title=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )

    st.plotly_chart(
        theme_fig,
        use_container_width=True,
        config={"displayModeBar": False},
    )

with right:
    heat_source = (
        df.groupby(
            [
                "Edition Country",
                "Primary Category",
            ]
        )["Governance Risk Score"]
        .mean()
        .reset_index()
    )

    heat_pivot = heat_source.pivot(
        index="Edition Country",
        columns="Primary Category",
        values="Governance Risk Score",
    )

    heat_fig = go.Figure(
        data=go.Heatmap(
            z=heat_pivot.values,
            x=heat_pivot.columns.tolist(),
            y=heat_pivot.index.tolist(),
            colorbar=dict(
                title="AI-GRS",
            ),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Theme: %{x}<br>"
                "Average AI-GRS: %{z:.1f}"
                "<extra></extra>"
            ),
        )
    )

    heat_fig.update_layout(
        height=max(
            390,
            58 * len(heat_pivot.index),
        ),
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=80,
        ),
        xaxis=dict(
            title="",
            tickangle=-35,
        ),
        yaxis=dict(
            title="News edition country",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(
        heat_fig,
        use_container_width=True,
        config={"displayModeBar": False},
    )


# ---------------------------
# Geography
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Geographic exposure</div>',
    unsafe_allow_html=True,
)
st.subheader("Where are governance narratives emerging?")

country_summary["Marker Size"] = (
    country_summary["Narrative_Count"].clip(
        lower=1
    )
    * 6
    + 10
)

map_fig = go.Figure()

map_fig.add_trace(
    go.Scattergeo(
        lon=country_summary["Edition Longitude"],
        lat=country_summary["Edition Latitude"],
        text=(
            country_summary["Edition Country"]
            + "<br>Narratives: "
            + country_summary["Narrative_Count"].astype(str)
            + "<br>Avg AI-GRS: "
            + country_summary["Avg_Risk"].astype(str)
            + "<br>Avg sentiment: "
            + country_summary["Avg_Sentiment"].astype(str)
        ),
        mode="markers",
        marker=dict(
            size=country_summary["Marker Size"],
            color=country_summary["Avg_Risk"],
            colorscale="YlOrRd",
            showscale=True,
            colorbar=dict(
                title="AI-GRS",
            ),
            line=dict(
                width=.6,
                color="white",
            ),
            opacity=.82,
        ),
        hovertemplate="%{text}<extra></extra>",
    )
)

map_fig.update_layout(
    height=500,
    geo=dict(
        showland=True,
        landcolor="rgb(244, 247, 249)",
        countrycolor="rgb(214, 221, 227)",
        showcountries=True,
        bgcolor="rgba(0,0,0,0)",
    ),
    margin=dict(
        l=0,
        r=0,
        t=0,
        b=0,
    ),
    paper_bgcolor="rgba(0,0,0,0)",
)

st.plotly_chart(
    map_fig,
    use_container_width=True,
    config={"displayModeBar": False},
)

st.caption(
    "Geography represents the selected Google News language/country "
    "edition used for collection, not the precise location of a reader "
    "or source."
)


# ---------------------------
# Radar + narrative landscape
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Governance profile</div>',
    unsafe_allow_html=True,
)
st.subheader("How is the governance risk profile shaped?")

radar_left, radar_right = st.columns([.9, 1.1])

with radar_left:
    radar_df = category_overall.sort_values(
        "Avg_Risk",
        ascending=False,
    )

    radar_categories = (
        radar_df["Primary Category"]
        .astype(str)
        .tolist()
    )
    radar_values = (
        radar_df["Avg_Risk"]
        .astype(float)
        .tolist()
    )

    if radar_categories:
        radar_categories_closed = (
            radar_categories
            + [radar_categories[0]]
        )
        radar_values_closed = (
            radar_values
            + [radar_values[0]]
        )

        radar = go.Figure(
            go.Scatterpolar(
                r=radar_values_closed,
                theta=radar_categories_closed,
                fill="toself",
                name=display_name,
                hovertemplate=(
                    "<b>%{theta}</b><br>"
                    "AI-GRS: %{r:.1f}"
                    "<extra></extra>"
                ),
            )
        )

        radar.update_layout(
            height=500,
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    gridcolor="rgba(100,120,140,.14)",
                ),
            ),
            margin=dict(
                l=45,
                r=45,
                t=20,
                b=20,
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )

        st.plotly_chart(
            radar,
            use_container_width=True,
            config={"displayModeBar": False},
        )

with radar_right:
    landscape = go.Figure()

    landscape.add_trace(
        go.Scatter(
            x=df["Sentiment"],
            y=df["Governance Risk Score"],
            mode="markers",
            marker=dict(
                size=(
                    10
                    + df["Governance Risk Score"].clip(
                        lower=0
                    )
                    / 4
                ),
                opacity=.68,
                line=dict(width=.5),
            ),
            text=df["Headline"],
            customdata=df[
                [
                    "Edition Country",
                    "Language",
                    "Primary Category",
                    "Source",
                ]
            ],
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Country edition: %{customdata[0]}<br>"
                "Language: %{customdata[1]}<br>"
                "Theme: %{customdata[2]}<br>"
                "Source: %{customdata[3]}<br>"
                "Sentiment: %{x:.3f}<br>"
                "AI-GRS: %{y:.1f}"
                "<extra></extra>"
            ),
        )
    )

    landscape.add_hline(
        y=60,
        line_dash="dash",
        opacity=.35,
    )

    landscape.add_vline(
        x=0,
        line_dash="dot",
        opacity=.25,
    )

    landscape.update_layout(
        height=500,
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=30,
        ),
        xaxis=dict(
            title="Sentiment ← negative | positive →",
            range=[-1, 1],
            gridcolor="rgba(100,120,140,.12)",
            zeroline=False,
        ),
        yaxis=dict(
            title="AI Governance Risk",
            range=[0, 100],
            gridcolor="rgba(100,120,140,.12)",
            zeroline=False,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )

    st.plotly_chart(
        landscape,
        use_container_width=True,
        config={"displayModeBar": False},
    )


# ---------------------------
# Priority queue
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Priority narratives</div>',
    unsafe_allow_html=True,
)
st.subheader("What requires governance attention now?")

priority_df = (
    df.sort_values(
        "Governance Risk Score",
        ascending=False,
    )
    .copy()
)

priority_df["Priority"] = priority_df[
    "Governance Risk Score"
].apply(
    lambda value:
    "Critical"
    if value >= 75
    else (
        "Elevated"
        if value >= 60
        else "Monitor"
    )
)

priority_view = priority_df.head(12)[
    [
        "Priority",
        "Primary Category",
        "Edition Country",
        "Language",
        "Headline",
        "Source",
        "Governance Risk Score",
        "Sentiment",
    ]
].copy()

st.dataframe(
    priority_view,
    use_container_width=True,
    hide_index=True,
)


# ---------------------------
# Audit evidence and methodology
# ---------------------------
with st.expander(
    "Full risk-ranked AI governance evidence"
):
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
        .sort_values(
            by="Governance Risk Score",
            ascending=False,
        )
        .reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )

with st.expander(
    "Governance taxonomy and inclusion rule"
):
    st.write(
        "The module creates a focused research corpus by combining the "
        "selected organisation query with AI-governance categories. "
        "In strict mode, a headline or summary must contain at least "
        "one governance keyword."
    )

    taxonomy_rows = []

    for category, keywords in CATEGORY_KEYWORDS.items():
        taxonomy_rows.append(
            {
                "Category": category,
                "Core English Keywords": ", ".join(
                    keywords
                ),
            }
        )

    st.dataframe(
        pd.DataFrame(taxonomy_rows),
        use_container_width=True,
        hide_index=True,
    )

with st.expander(
    "Search queries used in this run"
):
    query_df = (
        df[
            [
                "Language",
                "Edition Country",
                "Edition Region",
                "Primary Category",
                "Entity Query",
                "Search Query",
            ]
        ]
        .drop_duplicates()
        .sort_values(
            by=[
                "Edition Country",
                "Language",
                "Primary Category",
            ]
        )
    )

    st.dataframe(
        query_df,
        use_container_width=True,
        hide_index=True,
    )

with st.expander(
    "Methodology and model limitations"
):
    st.info(
        "Multilingual collection uses Google News language/country "
        "editions and language-specific keyword taxonomies. "
        "English sentiment uses VADER/TextBlob; other languages use "
        "prototype lexicons that require further validation. "
        "AI-GRS is a prototype governance-risk indicator for comparative "
        "decision support, not an automated legal or compliance judgment."
    )
