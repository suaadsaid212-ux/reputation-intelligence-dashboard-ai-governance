import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.entity_selector import (
    get_entity,
    get_entity_query,
)
from utils.glossary import metric_help, render_glossary
from utils.multilingual_content import (
    fetch_multilingual_news,
    get_selected_content_languages,
    safe_sentiment_stats,
)


st.set_page_config(
    page_title="Crisis Intelligence Command Center",
    page_icon="🚨",
    layout="wide",
)

entity = get_entity()

entity_name = entity["Entity_Name"]
display_name = entity["Short_Name"]

news_query = get_entity_query(
    entity,
    "News_Query",
)

trends_query = get_entity_query(
    entity,
    "Google_Trends_Query",
)

youtube_query = get_entity_query(
    entity,
    "YouTube_Query",
)

priority = entity["Priority"]

ticker = str(
    entity.get(
        "Ticker",
        "",
    )
).strip()

cik = str(
    entity.get(
        "CIK",
        "",
    )
).strip()

st.title("Crisis Intelligence Command Center")

st.markdown(
    """
    <div class="ti-live">
        <span class="ti-live-dot"></span>
        <span>Live multilingual crisis narrative monitoring</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    f"{display_name} • {entity['Country']} • {entity['Sector']} • "
    "Early-warning view across multilingual news and supporting risk proxies"
)

render_glossary(
    [
        "RII",
        "OLI",
        "SRI",
    ]
)

content_languages = get_selected_content_languages()


def has_value(value):
    text = str(value).strip()
    return (
        bool(text)
        and text.lower() != "nan"
    )


@st.cache_data(
    ttl=1800,
    show_spinner=False,
)
def load_news(
    query,
    languages,
):
    return fetch_multilingual_news(
        query,
        languages=list(languages),
        limit_per_language=8,
    )


with st.spinner(
    "Scanning multilingual crisis narratives..."
):
    news_df = load_news(
        news_query,
        tuple(content_languages),
    )


stats = safe_sentiment_stats(
    news_df
)

if stats["count"]:
    news_risk = round(
        min(
            100.0,
            (
                min(
                    1.0,
                    stats["count"]
                    / max(
                        25,
                        len(
                            content_languages
                        )
                        * 8,
                    ),
                )
                * 35
                + stats[
                    "negative_ratio"
                ]
                * 45
                + stats[
                    "std"
                ]
                * 20
            ),
        ),
        2,
    )
else:
    news_risk = 20.0


# These remain the existing prototype availability proxies.
search_risk = (
    65
    if has_value(
        trends_query
    )
    else 35
)

social_risk = (
    60
    if has_value(
        youtube_query
    )
    else 35
)

priority_risk = {
    "Critical": 75,
    "High": 60,
    "Medium": 45,
    "Low": 30,
}.get(
    priority,
    45,
)

financial_risk = (
    65
    if (
        has_value(ticker)
        or has_value(cik)
    )
    else 40
)

rii_risk = round(
    min(
        100.0,
        (
            news_risk * 0.50
            + financial_risk * 0.25
            + priority_risk * 0.25
        ),
    ),
    2,
)

oli_risk = round(
    max(
        0.0,
        100
        - (
            priority_risk * 0.40
            + search_risk * 0.25
            + social_risk * 0.20
            + financial_risk * 0.15
        ),
    ),
    2,
)

crisis_score = round(
    (
        news_risk * 0.35
        + social_risk * 0.20
        + search_risk * 0.20
        + rii_risk * 0.15
        + oli_risk * 0.10
    ),
    2,
)

if crisis_score <= 20:
    level = "Normal"
    response_posture = "Standard monitoring"
elif crisis_score <= 40:
    level = "Watch"
    response_posture = "Increase observation"
elif crisis_score <= 60:
    level = "Elevated"
    response_posture = "Focused review"
elif crisis_score <= 80:
    level = "High Risk"
    response_posture = "Escalated monitoring"
else:
    level = "Crisis Alert"
    response_posture = "Immediate response"


languages_observed = (
    int(
        news_df[
            "Language"
        ].nunique()
    )
    if not news_df.empty
    else 0
)

negative_share = round(
    float(
        stats.get(
            "negative_ratio",
            0.0,
        )
        * 100
    ),
    1,
)

narrative_count = int(
    stats.get(
        "count",
        0,
    )
)


# ---------------------------
# Alert level
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Current threat posture</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="ti-threat">
        <div class="ti-threat-kicker">Current Early-Warning Status</div>
        <div class="ti-threat-level">{level} • {crisis_score:.1f}/100</div>
        <div class="ti-threat-copy">
            <strong>{display_name}</strong> is currently in a
            <strong>{response_posture}</strong> posture.
            The live multilingual news component is
            <strong>{news_risk:.1f}</strong>, with
            <strong>{negative_share:.1f}%</strong> of current monitored
            narratives classified as negative.
            Search and social inputs shown below remain prototype
            readiness proxies unless their dedicated live modules are integrated.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric(
    "Crisis Score",
    f"{crisis_score:.1f}",
)

k2.metric(
    "News Risk",
    f"{news_risk:.1f}",
)

k3.metric(
    "Negative Narrative Share",
    f"{negative_share:.1f}%",
)

k4.metric(
    "Narratives Scanned",
    narrative_count,
)

k5.metric(
    "Languages Observed",
    languages_observed,
)


# ---------------------------
# Gauge + signal composition
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Signal composition</div>',
    unsafe_allow_html=True,
)
st.subheader("What is driving the current alert level?")

gauge_col, radar_col = st.columns([.9, 1.1])

with gauge_col:
    gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=crisis_score,
            title={
                "text": "Crisis Risk Score"
            },
            gauge={
                "axis": {
                    "range": [
                        0,
                        100,
                    ]
                },
                "bar": {
                    "thickness": .32,
                },
                "steps": [
                    {
                        "range": [
                            0,
                            20,
                        ],
                        "color": "rgba(120,130,140,.07)",
                    },
                    {
                        "range": [
                            20,
                            40,
                        ],
                        "color": "rgba(120,130,140,.11)",
                    },
                    {
                        "range": [
                            40,
                            60,
                        ],
                        "color": "rgba(120,130,140,.15)",
                    },
                    {
                        "range": [
                            60,
                            80,
                        ],
                        "color": "rgba(120,130,140,.20)",
                    },
                    {
                        "range": [
                            80,
                            100,
                        ],
                        "color": "rgba(120,130,140,.26)",
                    },
                ],
                "threshold": {
                    "line": {
                        "width": 3,
                    },
                    "thickness": .75,
                    "value": crisis_score,
                },
            },
        )
    )

    gauge.update_layout(
        height=420,
        margin=dict(
            l=25,
            r=25,
            t=60,
            b=20,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(
        gauge,
        use_container_width=True,
        config={
            "displayModeBar": False,
        },
    )

with radar_col:
    risk_sources = [
        "News",
        "Social Proxy",
        "Search Proxy",
        "RII",
        "OLI",
    ]

    risk_values = [
        news_risk,
        social_risk,
        search_risk,
        rii_risk,
        oli_risk,
    ]

    radar = go.Figure(
        go.Scatterpolar(
            r=(
                risk_values
                + [
                    risk_values[0]
                ]
            ),
            theta=(
                risk_sources
                + [
                    risk_sources[0]
                ]
            ),
            fill="toself",
            hovertemplate=(
                "<b>%{theta}</b><br>"
                "Signal score: %{r:.1f}"
                "<extra></extra>"
            ),
        )
    )

    radar.update_layout(
        height=420,
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[
                    0,
                    100,
                ],
            ),
        ),
        margin=dict(
            l=40,
            r=40,
            t=30,
            b=30,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )

    st.plotly_chart(
        radar,
        use_container_width=True,
        config={
            "displayModeBar": False,
        },
    )


# ---------------------------
# Multilingual pressure
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Multilingual pressure</div>',
    unsafe_allow_html=True,
)
st.subheader("Where is negative narrative pressure concentrated?")

if news_df.empty:
    st.info(
        "No live multilingual news headlines were returned for the current entity."
    )
else:
    language_summary = (
        news_df.groupby(
            "Language"
        )
        .agg(
            Narratives=(
                "Headline",
                "count",
            ),
            Average_Sentiment=(
                "Sentiment",
                "mean",
            ),
            Negative_Share=(
                "Sentiment",
                lambda values:
                float(
                    (
                        values
                        <= -0.05
                    )
                    .mean()
                    * 100
                ),
            ),
        )
        .reset_index()
    )

    language_summary[
        "Average Sentiment"
    ] = (
        language_summary[
            "Average_Sentiment"
        ]
        .round(3)
    )

    language_summary[
        "Negative Share %"
    ] = (
        language_summary[
            "Negative_Share"
        ]
        .round(1)
    )

    language_summary[
        "Pressure Score"
    ] = (
        (
            language_summary[
                "Negative Share %"
            ]
            * .65
        )
        + (
            language_summary[
                "Narratives"
            ]
            .rank(
                pct=True,
                method="average",
            )
            * 100
            * .35
        )
    ).clip(
        0,
        100,
    ).round(1)

    lang_left, lang_right = st.columns(
        [1, 1.1]
    )

    with lang_left:
        lang_rank = (
            language_summary.sort_values(
                "Pressure Score",
                ascending=True,
            )
        )

        lang_fig = go.Figure(
            go.Bar(
                x=lang_rank[
                    "Pressure Score"
                ],
                y=lang_rank[
                    "Language"
                ],
                orientation="h",
                text=lang_rank[
                    "Pressure Score"
                ],
                textposition="outside",
                customdata=np.stack(
                    [
                        lang_rank[
                            "Narratives"
                        ],
                        lang_rank[
                            "Negative Share %"
                        ],
                        lang_rank[
                            "Average Sentiment"
                        ],
                    ],
                    axis=-1,
                ),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Pressure Score: %{x:.1f}<br>"
                    "Narratives: %{customdata[0]}<br>"
                    "Negative Share: %{customdata[1]:.1f}%<br>"
                    "Average Sentiment: %{customdata[2]:.3f}"
                    "<extra></extra>"
                ),
            )
        )

        lang_fig.update_layout(
            height=max(
                360,
                54
                * len(
                    lang_rank
                ),
            ),
            margin=dict(
                l=10,
                r=50,
                t=10,
                b=25,
            ),
            xaxis=dict(
                title="Narrative Pressure",
                range=[
                    0,
                    100,
                ],
                showgrid=True,
                zeroline=False,
            ),
            yaxis=dict(
                title="",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )

        st.plotly_chart(
            lang_fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
            },
        )

    with lang_right:
        scatter = go.Figure(
            go.Scatter(
                x=language_summary[
                    "Average Sentiment"
                ],
                y=language_summary[
                    "Negative Share %"
                ],
                mode="markers+text",
                text=language_summary[
                    "Language"
                ],
                textposition="top center",
                marker=dict(
                    size=(
                        18
                        + 32
                        * (
                            language_summary[
                                "Narratives"
                            ]
                            / max(
                                language_summary[
                                    "Narratives"
                                ]
                                .max(),
                                1,
                            )
                        )
                    ),
                    opacity=.72,
                    line=dict(
                        width=.6,
                    ),
                ),
                customdata=language_summary[
                    [
                        "Narratives",
                        "Pressure Score",
                    ]
                ],
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Average Sentiment: %{x:.3f}<br>"
                    "Negative Share: %{y:.1f}%<br>"
                    "Narratives: %{customdata[0]}<br>"
                    "Pressure Score: %{customdata[1]:.1f}"
                    "<extra></extra>"
                ),
            )
        )

        scatter.update_layout(
            height=420,
            margin=dict(
                l=20,
                r=20,
                t=20,
                b=35,
            ),
            xaxis=dict(
                title="Average Sentiment",
                range=[
                    -1,
                    1,
                ],
                showgrid=True,
                zeroline=False,
            ),
            yaxis=dict(
                title="Negative Narrative Share %",
                range=[
                    0,
                    100,
                ],
                showgrid=True,
                zeroline=False,
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )

        st.plotly_chart(
            scatter,
            use_container_width=True,
            config={
                "displayModeBar": False,
            },
        )


# ---------------------------
# News-based timeline
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Narrative trajectory</div>',
    unsafe_allow_html=True,
)
st.subheader("How is news pressure changing over time?")

timeline_available = False

if (
    not news_df.empty
    and "Published"
    in news_df.columns
):
    timeline_df = news_df.copy()

    timeline_df[
        "Published Parsed"
    ] = pd.to_datetime(
        timeline_df[
            "Published"
        ],
        errors="coerce",
        utc=True,
    )

    timeline_df = (
        timeline_df.dropna(
            subset=[
                "Published Parsed"
            ]
        )
        .copy()
    )

    if not timeline_df.empty:
        timeline_df[
            "Date"
        ] = timeline_df[
            "Published Parsed"
        ].dt.date

        daily = (
            timeline_df.groupby(
                "Date"
            )
            .agg(
                Narratives=(
                    "Headline",
                    "count",
                ),
                Average_Sentiment=(
                    "Sentiment",
                    "mean",
                ),
                Negative_Share=(
                    "Sentiment",
                    lambda values:
                    float(
                        (
                            values
                            <= -0.05
                        )
                        .mean()
                        * 100
                    ),
                ),
            )
            .reset_index()
        )

        if len(daily) >= 2:
            timeline_available = True

            daily[
                "Narrative Pressure"
            ] = (
                daily[
                    "Negative_Share"
                ]
                * .65
                + daily[
                    "Narratives"
                ]
                .rank(
                    pct=True,
                    method="average",
                )
                * 100
                * .35
            ).clip(
                0,
                100,
            )

            time_fig = go.Figure()

            time_fig.add_trace(
                go.Scatter(
                    x=daily[
                        "Date"
                    ],
                    y=daily[
                        "Narrative Pressure"
                    ],
                    mode="lines+markers",
                    name="Narrative Pressure",
                    fill="tozeroy",
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        "Narrative Pressure: %{y:.1f}"
                        "<extra></extra>"
                    ),
                )
            )

            time_fig.update_layout(
                height=390,
                margin=dict(
                    l=20,
                    r=20,
                    t=15,
                    b=30,
                ),
                xaxis=dict(
                    title="Publication date",
                ),
                yaxis=dict(
                    title="Derived Narrative Pressure",
                    range=[
                        0,
                        100,
                    ],
                    showgrid=True,
                    zeroline=False,
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
            )

            st.plotly_chart(
                time_fig,
                use_container_width=True,
                config={
                    "displayModeBar": False,
                },
            )

if not timeline_available:
    st.info(
        "A reliable multi-date news timeline is not available in the current evidence set."
    )


# ---------------------------
# Response posture
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Response posture</div>',
    unsafe_allow_html=True,
)
st.subheader("What should the monitoring team do next?")

if crisis_score > 80:
    response_cards = [
        (
            "Immediate Escalation",
            "Activate the crisis-response workflow and assign clear ownership.",
        ),
        (
            "Multilingual Watch",
            "Increase monitoring across the languages and editions showing the strongest pressure.",
        ),
        (
            "Stakeholder Response",
            "Prepare evidence-led internal and external response options.",
        ),
    ]
elif crisis_score > 60:
    response_cards = [
        (
            "Escalated Monitoring",
            "Increase review frequency for high-risk narratives and languages.",
        ),
        (
            "Cross-Channel Check",
            "Compare the news signal with live social and search modules before escalation.",
        ),
        (
            "Response Readiness",
            "Prepare stakeholder messaging and decision thresholds.",
        ),
    ]
elif crisis_score > 40:
    response_cards = [
        (
            "Focused Review",
            "Review the most negative multilingual narratives and their sources.",
        ),
        (
            "Trend Validation",
            "Check whether the same issue is appearing in social and search signals.",
        ),
        (
            "Monitor Escalation",
            "Watch for increasing volume, negativity or cross-language spread.",
        ),
    ]
else:
    response_cards = [
        (
            "Standard Monitoring",
            "Maintain routine multilingual monitoring.",
        ),
        (
            "Baseline Tracking",
            "Keep current narrative and language levels as a comparison baseline.",
        ),
        (
            "Validate Changes",
            "Escalate only when multiple independent signals begin to strengthen.",
        ),
    ]

cards_html = "".join(
    [
        f"""
        <div class="ti-response-card">
            <div class="ti-response-title">{title}</div>
            <div class="ti-response-copy">{copy}</div>
        </div>
        """
        for title, copy in response_cards
    ]
)

st.markdown(
    f"""
    <div class="ti-response-grid">
        {cards_html}
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------
# Priority headlines
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Priority evidence</div>',
    unsafe_allow_html=True,
)
st.subheader("Which narratives require attention?")

if news_df.empty:
    st.info(
        "No live multilingual news headlines found for this entity."
    )
else:
    priority_news = (
        news_df.copy()
        .sort_values(
            "Sentiment"
        )
        .head(15)
    )

    display_columns = [
        "Headline",
        "Language",
        "Edition Country",
        "Source",
        "Sentiment",
        "Sentiment Label",
        "Published",
        "Link",
    ]

    st.dataframe(
        priority_news[
            [
                column
                for column
                in display_columns
                if column
                in priority_news.columns
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    with st.expander(
        "Full crisis evidence audit"
    ):
        st.dataframe(
            news_df,
            use_container_width=True,
            hide_index=True,
        )


# ---------------------------
# Methodology
# ---------------------------
with st.expander(
    "Crisis score methodology and limitations"
):
    st.write(
        "The current Crisis Score is a prototype composite using multilingual "
        "news risk, social and search readiness proxies, RII risk and OLI risk. "
        "The multilingual news component is calculated from current narrative volume, "
        "negative share and sentiment volatility."
    )

    st.write(
        "The social and search values on this page are not presented as live measurements "
        "unless those modules are technically integrated into a shared live state. "
        "In the current implementation they remain availability/readiness proxies inherited "
        "from the original prototype logic."
    )

    st.write(
        "The Narrative Pressure timeline, when available, is derived only from the current "
        "news evidence set using daily volume and negative share. It is not a historical "
        "Crisis Score series."
    )
