import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

from utils.chart_theme import RISK_SCALE, categorical_colors, risk_color
from utils.glossary import metric_help, render_glossary
from utils.live_ops import render_live_status
from utils.multilingual_content import (
    fetch_multilingual_news,
    get_selected_content_languages,
    language_coverage,
    safe_sentiment_stats,
)


st.set_page_config(
    page_title="Executive Overview",
    page_icon="📊",
    layout="wide",
)

st.title("Executive Intelligence Command Center")

render_live_status(
    [
        ("Multilingual News", "LIVE"),
        ("Page cache", "CACHED"),
        ("Market data", "CACHED"),
        ("Risk scoring", "PROTOTYPE"),
    ],
    note=(
        "News and market sources are current public connectors with cache windows "
        "for performance. Reputation Risk is a prototype comparative indicator."
    ),
)

render_glossary(["DSS", "RII", "OLI", "SRI", "VADER"])

try:
    registry_df = pd.read_csv(
        "config/entity_registry.csv",
        encoding="utf-8-sig",
    )
except FileNotFoundError:
    st.error("Registry file not found: config/entity_registry.csv")
    st.stop()

time_range = st.sidebar.selectbox(
    "Analysis Period",
    [
        "1 Month",
        "3 Months",
        "6 Months",
        "1 Year",
        "3 Years",
        "5 Years",
    ],
)

start_dates = {
    "1 Month": "2026-05-01",
    "3 Months": "2026-03-01",
    "6 Months": "2025-12-01",
    "1 Year": "2025-06-01",
    "3 Years": "2023-06-01",
    "5 Years": "2021-06-01",
}

start_date = start_dates[time_range]

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
        filtered_registry["Sector"].isin(
            sector_filter
        )
    ]

if priority_filter:
    filtered_registry = filtered_registry[
        filtered_registry["Priority"].isin(
            priority_filter
        )
    ]

selected_entities = st.sidebar.multiselect(
    "Select Organizations",
    filtered_registry["Entity_Name"].tolist(),
    default=(
        filtered_registry["Entity_Name"]
        .head(5)
        .tolist()
    ),
)

if not selected_entities:
    st.warning("Select at least one organization.")
    st.stop()

selected_df = filtered_registry[
    filtered_registry["Entity_Name"].isin(
        selected_entities
    )
]

content_languages = get_selected_content_languages()


def has_value(value):
    text = str(value).strip()
    return bool(text) and text.lower() != "nan"


@st.cache_data(ttl=1800, show_spinner=False)
def get_news_scores(query, languages):
    return fetch_multilingual_news(
        query=query,
        languages=list(languages),
        limit_per_language=6,
    )


@st.cache_data(ttl=3600, show_spinner=False)
def get_market_volatility(ticker, start_date):
    if not has_value(ticker):
        return 0.0

    try:
        stock = yf.download(
            ticker,
            start=start_date,
            progress=False,
            auto_adjust=True,
        )
    except Exception:
        return 0.0

    if stock.empty:
        return 0.0

    stock["Returns"] = stock["Close"].pct_change()

    volatility = (
        stock["Returns"]
        .rolling(21)
        .std()
        .dropna()
    )

    if volatility.empty:
        return 0.0

    value = volatility.iloc[-1]

    try:
        return float(value)
    except Exception:
        return float(value.squeeze())


results = []
negative_rows = []
all_news = []

with st.spinner("Collecting multilingual evidence..."):
    for _, entity in selected_df.iterrows():
        query = entity["News_Query"]

        news_df = get_news_scores(
            query,
            tuple(content_languages),
        )

        if news_df.empty:
            continue

        news_df = news_df.copy()
        news_df["Entity"] = entity["Short_Name"]

        all_news.append(news_df)

        stats = safe_sentiment_stats(news_df)

        market_volatility = get_market_volatility(
            entity["Ticker"],
            start_date,
        )

        dss = stats["abs_mean"]
        sentiment_volatility = stats["std"]

        reputation_risk = min(
            100.0,
            sentiment_volatility * 45
            + dss * 35
            + market_volatility * 20,
        )

        if reputation_risk >= 70:
            risk_level = "High"
        elif reputation_risk >= 40:
            risk_level = "Elevated"
        else:
            risk_level = "Low"

        results.append(
            {
                "Entity": entity["Entity_Name"],
                "Short Name": entity["Short_Name"],
                "Ticker": entity["Ticker"],
                "Country": entity["Country"],
                "Sector": entity["Sector"],
                "Narratives": stats["count"],
                "Languages": int(
                    news_df["Language"].nunique()
                ),
                "Average Sentiment": round(
                    stats["mean"],
                    3,
                ),
                "Negative Share %": round(
                    stats["negative_ratio"] * 100,
                    1,
                ),
                "DSS": round(dss, 3),
                "Narrative Volatility": round(
                    sentiment_volatility,
                    3,
                ),
                "Market Volatility": round(
                    market_volatility,
                    4,
                ),
                "Reputation Risk": round(
                    reputation_risk,
                    2,
                ),
                "Risk Level": risk_level,
            }
        )

        entity_negative = news_df[
            news_df["Sentiment"] <= -0.3
        ].copy()

        if not entity_negative.empty:
            entity_negative["Entity"] = entity[
                "Short_Name"
            ]
            negative_rows.append(entity_negative)

risk_df = pd.DataFrame(results)

if risk_df.empty:
    st.error(
        "No multilingual news data available. "
        "Try fewer languages or different organizations."
    )
    st.stop()

ranking_df = risk_df.sort_values(
    by="Reputation Risk",
    ascending=False,
).copy()

ranking_df["Rank"] = range(
    1,
    len(ranking_df) + 1,
)

combined_news = (
    pd.concat(
        all_news,
        ignore_index=True,
    )
    if all_news
    else pd.DataFrame()
)

coverage_df = (
    language_coverage(combined_news)
    if not combined_news.empty
    else pd.DataFrame()
)

avg_rr = round(
    risk_df["Reputation Risk"].mean(),
    2,
)

highest = ranking_df.iloc[0]
highest_entity = highest["Short Name"]
highest_risk = float(highest["Reputation Risk"])

high_risk_count = int(
    risk_df["Reputation Risk"].ge(70).sum()
)

total_narratives = int(
    risk_df["Narratives"].sum()
)

languages_observed = int(
    combined_news["Language"].nunique()
    if not combined_news.empty
    else 0
)

dominant_language = (
    coverage_df.iloc[0]["Language"]
    if not coverage_df.empty
    else "N/A"
)

most_negative_entity = (
    risk_df.sort_values(
        "Negative Share %",
        ascending=False,
    )
    .iloc[0]["Short Name"]
)

st.markdown(
    f"""
    <div class="ti-live">
        <span>
            {len(risk_df)} organizations monitored
            &nbsp;•&nbsp;
            {languages_observed} languages observed
            &nbsp;•&nbsp;
            {total_narratives} narratives analysed
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="ti-section-label">Executive status</div>',
    unsafe_allow_html=True,
)

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric(
    "Average Reputation Risk",
    avg_rr,
)
k2.metric(
    "Highest Risk Entity",
    highest_entity,
)
k3.metric(
    "High-Risk Organizations",
    high_risk_count,
)
k4.metric(
    "Narratives Analysed",
    total_narratives,
)
k5.metric(
    "Languages Observed",
    languages_observed,
)

brief_text = (
    f"<strong>{highest_entity}</strong> currently has the highest "
    f"reputation-risk score at <strong>{highest_risk:.1f}</strong>. "
    f"<strong>{dominant_language}</strong> is the largest evidence-language "
    f"cluster in the current monitoring set. "
    f"<strong>{most_negative_entity}</strong> shows the highest share of "
    f"negative narratives. "
)

if high_risk_count > 0:
    brief_text += (
        f"<strong>{high_risk_count}</strong> organization(s) currently "
        f"meet the high-risk threshold and should be reviewed first."
    )
else:
    brief_text += (
        "No organization currently meets the high-risk threshold, "
        "but elevated entities should remain under active monitoring."
    )

st.markdown(
    f"""
    <div class="ti-brief">
        <div class="ti-brief-kicker">Executive Brief</div>
        <div class="ti-brief-text">{brief_text}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="ti-section-label">Portfolio intelligence</div>',
    unsafe_allow_html=True,
)
st.subheader("Who needs attention first?")

left, right = st.columns([1.35, 1])

with left:
    risk_chart_df = ranking_df.sort_values(
        "Reputation Risk",
        ascending=True,
    )

    bar = go.Figure(
        go.Bar(
            x=risk_chart_df["Reputation Risk"],
            y=risk_chart_df["Short Name"],
            orientation="h",
            text=risk_chart_df["Reputation Risk"],
            textposition="outside",
            marker=dict(
                color=[
                    risk_color(value)
                    for value in risk_chart_df["Reputation Risk"]
                ],
                line=dict(color="white", width=1),
            ),
            customdata=np.stack(
                [
                    risk_chart_df["Risk Level"],
                    risk_chart_df["Narratives"],
                    risk_chart_df["Languages"],
                ],
                axis=-1,
            ),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Reputation Risk: %{x:.1f}<br>"
                "Risk Level: %{customdata[0]}<br>"
                "Narratives: %{customdata[1]}<br>"
                "Languages: %{customdata[2]}"
                "<extra></extra>"
            ),
        )
    )

    bar.update_layout(
        height=max(
            360,
            72 * len(risk_chart_df),
        ),
        margin=dict(
            l=10,
            r=40,
            t=15,
            b=20,
        ),
        xaxis=dict(
            title="Reputation Risk",
            range=[0, 100],
            showgrid=True,
            gridcolor="rgba(100,120,140,.12)",
            zeroline=False,
        ),
        yaxis=dict(
            title="",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        transition=dict(duration=450, easing="cubic-in-out"),
    )

    st.plotly_chart(
        bar,
        use_container_width=True,
        config={
            "displayModeBar": False,
        },
    )

with right:
    if coverage_df.empty:
        st.info("No language coverage data available.")
    else:
        lang_display = coverage_df.copy()

        lang_display = lang_display.sort_values(
            "Narratives",
            ascending=True,
        )

        language_colors = categorical_colors(len(lang_display))

        lang_fig = go.Figure(
            go.Bar(
                x=lang_display["Narratives"],
                y=lang_display["Language"],
                orientation="h",
                text=lang_display["Narratives"],
                textposition="outside",
                marker=dict(
                    color=language_colors,
                    line=dict(color="white", width=1),
                ),
                customdata=np.stack(
                    [
                        lang_display["Average Sentiment"],
                        lang_display["Negative Share %"],
                    ],
                    axis=-1,
                ),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Narratives: %{x}<br>"
                    "Average Sentiment: %{customdata[0]:.3f}<br>"
                    "Negative Share: %{customdata[1]:.1f}%"
                    "<extra></extra>"
                ),
            )
        )

        lang_fig.update_layout(
            height=max(
                360,
                54 * len(lang_display),
            ),
            margin=dict(
                l=10,
                r=40,
                t=15,
                b=20,
            ),
            xaxis=dict(
                title="Narratives",
                showgrid=True,
                gridcolor="rgba(100,120,140,.12)",
                zeroline=False,
            ),
            yaxis=dict(
                title="",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            transition=dict(duration=450, easing="cubic-in-out"),
        )

        st.plotly_chart(
            lang_fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
            },
        )

st.markdown(
    '<div class="ti-section-label">Risk landscape</div>',
    unsafe_allow_html=True,
)
st.subheader("Narrative pressure vs reputation risk")

bubble = go.Figure()

bubble.add_trace(
    go.Scatter(
        x=risk_df["Average Sentiment"],
        y=risk_df["Reputation Risk"],
        mode="markers+text",
        text=risk_df["Short Name"],
        textposition="top center",
        marker=dict(
            size=(
                16
                + 34
                * (
                    risk_df["Narratives"]
                    / max(
                        risk_df["Narratives"].max(),
                        1,
                    )
                )
            ),
            color=risk_df["Reputation Risk"],
            colorscale=RISK_SCALE,
            cmin=0,
            cmax=100,
            showscale=True,
            colorbar=dict(
                title="Risk",
                thickness=12,
            ),
            opacity=0.78,
            line=dict(
                width=1,
                color="white",
            ),
        ),
        customdata=np.stack(
            [
                risk_df["Narratives"],
                risk_df["Negative Share %"],
                risk_df["Languages"],
                risk_df["Sector"],
            ],
            axis=-1,
        ),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Average Sentiment: %{x:.3f}<br>"
            "Reputation Risk: %{y:.1f}<br>"
            "Narratives: %{customdata[0]}<br>"
            "Negative Share: %{customdata[1]:.1f}%<br>"
            "Languages: %{customdata[2]}<br>"
            "Sector: %{customdata[3]}"
            "<extra></extra>"
        ),
    )
)

bubble.add_hline(
    y=70,
    line_dash="dash",
    opacity=0.35,
)

bubble.add_vline(
    x=0,
    line_dash="dot",
    opacity=0.28,
)

bubble.update_layout(
    height=520,
    margin=dict(
        l=20,
        r=20,
        t=20,
        b=35,
    ),
    xaxis=dict(
        title="Average Sentiment  ← negative | positive →",
        range=[
            min(-1.0, risk_df["Average Sentiment"].min() - 0.1),
            max(1.0, risk_df["Average Sentiment"].max() + 0.1),
        ],
        gridcolor="rgba(100,120,140,.12)",
        zeroline=False,
    ),
    yaxis=dict(
        title="Reputation Risk",
        range=[0, 100],
        gridcolor="rgba(100,120,140,.12)",
        zeroline=False,
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    showlegend=False,
    transition=dict(duration=500, easing="cubic-in-out"),
)

st.plotly_chart(
    bubble,
    use_container_width=True,
    config={
        "displayModeBar": False,
    },
)

st.markdown(
    '<div class="ti-section-label">Priority queue</div>',
    unsafe_allow_html=True,
)
st.subheader("What requires attention now?")

action_df = ranking_df[
    ranking_df["Reputation Risk"] >= 40
].copy()

if action_df.empty:
    st.success(
        "No organizations currently require elevated attention."
    )
else:
    action_df["Priority"] = action_df[
        "Reputation Risk"
    ].apply(
        lambda value:
        "Critical"
        if value >= 70
        else "Monitor"
    )

    action_df["Key Signal"] = action_df.apply(
        lambda row:
        f"{row['Negative Share %']:.0f}% negative share, "
        f"{row['Narrative Volatility']:.2f} volatility",
        axis=1,
    )

    action_df["Recommended Attention"] = action_df[
        "Reputation Risk"
    ].apply(
        lambda value:
        "Immediate review"
        if value >= 70
        else "Monitor closely"
    )

    st.dataframe(
        action_df[
            [
                "Priority",
                "Short Name",
                "Reputation Risk",
                "Key Signal",
                "Recommended Attention",
            ]
        ].rename(
            columns={
                "Short Name": "Organization",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

st.markdown(
    '<div class="ti-section-label">Evidence</div>',
    unsafe_allow_html=True,
)
st.subheader("Top risk narratives")

if negative_rows:
    negative_df = pd.concat(
        negative_rows,
        ignore_index=True,
    )

    negative_df = negative_df.sort_values(
        "Sentiment"
    ).head(15)

    evidence_view = negative_df[
        [
            "Entity",
            "Headline",
            "Language",
            "Source",
            "Sentiment",
            "Link",
        ]
    ].copy()

    st.dataframe(
        evidence_view,
        use_container_width=True,
        hide_index=True,
    )

    with st.expander(
        "Evidence details and analytical confidence"
    ):
        st.dataframe(
            negative_df[
                [
                    "Entity",
                    "Headline",
                    "Language",
                    "Edition Country",
                    "Source",
                    "Sentiment",
                    "Sentiment Method",
                    "Sentiment Confidence",
                    "Published",
                    "Link",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
else:
    st.info(
        "No high-risk negative narratives detected."
    )

with st.expander(
    "Detailed organization metrics"
):
    st.dataframe(
        ranking_df,
        use_container_width=True,
        hide_index=True,
    )

with st.expander(
    "Methodology note"
):
    st.info(
        "Multilingual sentiment outside English uses lightweight "
        "language-specific prototype lexicons. Original-language "
        "headlines are preserved and each record exposes its scoring "
        "method and confidence. DSS and market-volatility components "
        "remain available in the detailed metrics for analytical audit."
    )
