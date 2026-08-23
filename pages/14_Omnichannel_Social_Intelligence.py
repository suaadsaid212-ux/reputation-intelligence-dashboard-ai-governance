import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.chart_theme import MIXED_SCALE, RISK_SCALE, categorical_colors
from utils.entity_selector import get_entity, get_entity_query
from utils.section_export import render_section_export
from utils.live_ops import render_live_status
from utils.multilingual_content import (
    CONTENT_LANGUAGES,
    NEWS_PROFILES,
    detect_script_language,
    get_selected_content_languages,
    resolve_query_alias,
    score_multilingual_sentiment,
    sentiment_label,
)
from utils.social_expansion import (
    EXPANDED_PLATFORM_CATALOG,
    collect_expanded_social_narratives,
    cross_platform_terms,
    platform_comparison,
)


st.set_page_config(
    page_title="Omnichannel Social Intelligence Command Center",
    page_icon="🌐",
    layout="wide",
)


def get_secret_value(name):
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return value or os.environ.get(name, "")


@st.cache_data(ttl=1800, show_spinner=False)
def load_social(
    query,
    selected_platforms,
    youtube_api_key,
    limit_per_platform,
):
    return collect_expanded_social_narratives(
        query=query,
        selected_platforms=list(selected_platforms),
        youtube_api_key=youtube_api_key,
        limit_per_platform=limit_per_platform,
    )


entity = get_entity()
display_name = entity["Short_Name"]

default_query = (
    get_entity_query(entity, "YouTube_Query")
    or get_entity_query(entity, "Search_Query")
    or display_name
)

youtube_api_key = get_secret_value("YOUTUBE_API_KEY")

st.title("Omnichannel Social Intelligence Command Center")

render_live_status(
    [
        ("Public connectors", "ON-DEMAND"),
        ("Page cache", "CACHED"),
        ("Restricted platforms", "CONNECTOR-READY"),
        ("Risk scoring", "PROTOTYPE"),
    ],
    note=(
        "Live availability depends on the selected public source and credentials. "
        "Restricted platforms are not represented as live unless their connector is active."
    ),
)

st.caption(
    f"{display_name} • {entity['Country']} • {entity['Sector']} • "
    "Cross-platform, multilingual monitoring across public and approved sources"
)

platform_options = list(
    EXPANDED_PLATFORM_CATALOG.keys()
)

selected_platforms = st.sidebar.multiselect(
    "Platforms",
    platform_options,
    default=[
        "YouTube",
        "Reddit",
        "Hacker News",
        "Mastodon / Fediverse",
        "Bluesky",
    ],
)

base_query = st.sidebar.text_input(
    "Narrative query",
    value=default_query,
)

manual_aliases = st.sidebar.text_input(
    "Additional multilingual aliases",
    "",
)

limit_per_platform = st.sidebar.slider(
    "Maximum rows per live source",
    5,
    30,
    10,
    5,
)

content_languages = get_selected_content_languages()

language_name_by_code = {
    code: name
    for name, code in CONTENT_LANGUAGES.items()
}

search_plan = [
    (
        code,
        resolve_query_alias(
            base_query,
            code,
        ),
    )
    for code in content_languages
]

for alias in manual_aliases.split(","):
    alias = alias.strip()
    if alias:
        search_plan.append(
            (
                "custom",
                alias,
            )
        )

unique_plan = []
seen = set()

for code, current_query in search_plan:
    key = current_query.lower()
    if key in seen:
        continue
    seen.add(key)
    unique_plan.append(
        (
            code,
            current_query,
        )
    )

if st.sidebar.button("Refresh social data"):
    load_social.clear()

frames = []
coverage_frames = []
errors = []

with st.spinner(
    "Collecting multilingual omnichannel narratives..."
):
    for code, current_query in unique_plan:
        (
            posts_part,
            coverage_part,
            errors_part,
        ) = load_social(
            current_query,
            tuple(selected_platforms),
            youtube_api_key,
            limit_per_platform,
        )

        if not posts_part.empty:
            posts_part = posts_part.copy()

            posts_part[
                "Search Query Used"
            ] = current_query

            posts_part[
                "Search Language"
            ] = language_name_by_code.get(
                code,
                "Custom",
            )

            language_codes = []

            for _, row in posts_part.iterrows():
                fallback = (
                    code
                    if code in NEWS_PROFILES
                    else "en"
                )

                language_codes.append(
                    detect_script_language(
                        row.get(
                            "Text",
                            "",
                        ),
                        fallback,
                    )
                )

            posts_part[
                "Language Code"
            ] = language_codes

            posts_part[
                "Language"
            ] = [
                NEWS_PROFILES.get(
                    code_value,
                    {},
                ).get(
                    "label",
                    code_value,
                )
                for code_value in language_codes
            ]

            scores = []
            methods = []
            confidences = []

            for _, row in posts_part.iterrows():
                (
                    score,
                    method,
                    confidence,
                ) = score_multilingual_sentiment(
                    row.get(
                        "Text",
                        "",
                    ),
                    row[
                        "Language Code"
                    ],
                )

                scores.append(score)
                methods.append(method)
                confidences.append(
                    confidence
                )

            posts_part[
                "Sentiment"
            ] = scores

            posts_part[
                "Sentiment_Label"
            ] = [
                sentiment_label(score)
                for score in scores
            ]

            posts_part[
                "Sentiment Method"
            ] = methods

            posts_part[
                "Sentiment Confidence"
            ] = confidences

            frames.append(
                posts_part
            )

        if not coverage_part.empty:
            coverage_frames.append(
                coverage_part
            )

        errors.extend(
            errors_part
        )

if frames:
    posts = pd.concat(
        frames,
        ignore_index=True,
    )

    posts = (
        posts.drop_duplicates(
            subset=[
                "Platform",
                "Title",
                "Url",
            ],
            keep="first",
        )
        .reset_index(
            drop=True
        )
    )
else:
    posts = pd.DataFrame()

if coverage_frames:
    coverage = (
        pd.concat(
            coverage_frames,
            ignore_index=True,
        )
        .drop_duplicates()
    )
else:
    coverage = pd.DataFrame()

if posts.empty:
    st.warning(
        "No live public rows were returned for the current selection."
    )

    with st.expander(
        "Source coverage and connector readiness",
        expanded=True,
    ):
        st.dataframe(
            coverage,
            use_container_width=True,
            hide_index=True,
        )

        if errors:
            st.write("Connection notes")
            for error in sorted(set(errors)):
                st.write(error)

    st.stop()

comparison = platform_comparison(posts)

risk_posts = posts.copy()

risk_posts[
    "Risk Signal"
] = (
    (
        1
        - risk_posts[
            "Sentiment"
        ].fillna(0)
    )
    * 35
    + risk_posts[
        "Engagement"
    ]
    .fillna(0)
    .rank(
        pct=True,
        method="average",
    )
    * 30
).clip(
    0,
    100,
)

language_counts = (
    posts["Language"]
    .value_counts()
    .rename_axis("Language")
    .reset_index(name="Rows")
)

language_platform = (
    posts.groupby(
        [
            "Language",
            "Platform",
        ]
    )
    .size()
    .reset_index(
        name="Mentions"
    )
)

overlap = cross_platform_terms(
    posts,
    top_n=20,
)


# ---------------------------
# Executive KPIs
# ---------------------------
live_mentions = int(len(posts))

connected_platforms = int(
    posts["Platform"].nunique()
)

total_engagement = int(
    posts["Engagement"]
    .fillna(0)
    .sum()
)

languages_observed = int(
    posts["Language"].nunique()
)

if not comparison.empty:
    top_platform_row = (
        comparison.sort_values(
            "Platform Risk",
            ascending=False,
        )
        .iloc[0]
    )
    top_platform = top_platform_row[
        "Platform"
    ]
    top_platform_risk = float(
        top_platform_row[
            "Platform Risk"
        ]
    )
else:
    top_platform = "N/A"
    top_platform_risk = 0.0

top_language = (
    language_counts.iloc[0][
        "Language"
    ]
    if not language_counts.empty
    else "N/A"
)

top_risk_post = (
    risk_posts.sort_values(
        "Risk Signal",
        ascending=False,
    )
    .iloc[0]
)

top_risk_post_title = str(
    top_risk_post.get(
        "Title",
        "",
    )
)

if len(top_risk_post_title) > 120:
    top_risk_post_title = (
        top_risk_post_title[:117]
        + "..."
    )

st.markdown(
    '<div class="ti-section-label">Social intelligence status</div>',
    unsafe_allow_html=True,
)

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric(
    "Live Mentions",
    live_mentions,
)

k2.metric(
    "Highest-Risk Platform",
    top_platform,
)

k3.metric(
    "Connected Platforms",
    connected_platforms,
)

k4.metric(
    "Total Engagement",
    total_engagement,
)

k5.metric(
    "Languages Observed",
    languages_observed,
)


brief = (
    f"<strong>{top_platform}</strong> currently carries the highest "
    f"platform-risk score at <strong>{top_platform_risk:.1f}</strong>. "
    f"<strong>{top_language}</strong> is the most frequently observed "
    f"language in the current social evidence set. "
    f"The system has collected <strong>{live_mentions}</strong> live mentions "
    f"across <strong>{connected_platforms}</strong> connected platforms with "
    f"<strong>{total_engagement:,}</strong> total measured engagement. "
    f"The highest-ranked narrative signal is: "
    f"<strong>{top_risk_post_title}</strong>"
)

st.markdown(
    f"""
    <div class="ti-brief">
        <div class="ti-brief-kicker">Social Intelligence Brief</div>
        <div class="ti-brief-text">{brief}</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------
# Platform risk + metric matrix
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Platform intelligence</div>',
    unsafe_allow_html=True,
)
st.subheader("Where is narrative pressure concentrated?")

left, right = st.columns([1, 1.2])

with left:
    if comparison.empty:
        st.info(
            "No platform comparison data is available."
        )
    else:
        platform_rank = comparison.sort_values(
            "Platform Risk",
            ascending=True,
        )

        platform_fig = go.Figure(
            go.Bar(
                x=platform_rank[
                    "Platform Risk"
                ],
                y=platform_rank[
                    "Platform"
                ],
                orientation="h",
                text=platform_rank[
                    "Platform Risk"
                ],
                textposition="outside",
                marker=dict(
                    color=categorical_colors(len(platform_rank)),
                    line=dict(color="white", width=1),
                ),
                customdata=np.stack(
                    [
                        platform_rank[
                            "Mentions"
                        ],
                        platform_rank[
                            "Engagement"
                        ],
                        platform_rank[
                            "Negative Share %"
                        ],
                        platform_rank[
                            "Average Sentiment"
                        ],
                    ],
                    axis=-1,
                ),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Platform Risk: %{x:.1f}<br>"
                    "Mentions: %{customdata[0]}<br>"
                    "Engagement: %{customdata[1]}<br>"
                    "Negative Share: %{customdata[2]:.1f}%<br>"
                    "Average Sentiment: %{customdata[3]:.3f}"
                    "<extra></extra>"
                ),
            )
        )

        platform_fig.update_layout(
            height=max(
                390,
                64 * len(platform_rank),
            ),
            margin=dict(
                l=10,
                r=50,
                t=10,
                b=25,
            ),
            xaxis=dict(
                title="Platform Risk",
                range=[0, 100],
                showgrid=True,
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
            platform_fig,
            use_container_width=True,
            config={
                "displayModeBar": True, "displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 2},
            },
        )

        render_section_export(
            base_name=f"TrustIntel_{display_name}_Platform_Risk",
            data=platform_rank,
            figure=platform_fig,
            sheet_name="Platform Risk",
        )

with right:
    if comparison.empty:
        st.info(
            "No platform matrix is available."
        )
    else:
        heat_cols = [
            "Mention Share %",
            "Engagement Share %",
            "Negative Share %",
            "Platform Risk",
        ]

        heat_data = (
            comparison[
                [
                    "Platform",
                    *heat_cols,
                ]
            ]
            .set_index(
                "Platform"
            )
        )

        heat_fig = go.Figure(
            data=go.Heatmap(
                z=heat_data.values,
                x=heat_cols,
                y=heat_data.index.tolist(),
                colorscale=MIXED_SCALE,
                zmin=0,
                zmax=100,
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "%{x}: %{z:.1f}"
                    "<extra></extra>"
                ),
            )
        )

        heat_fig.update_layout(
            height=max(
                390,
                64 * len(heat_data.index),
            ),
            margin=dict(
                l=10,
                r=10,
                t=10,
                b=55,
            ),
            xaxis=dict(
                title="",
                tickangle=-20,
            ),
            yaxis=dict(
                title="",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            transition=dict(duration=450, easing="cubic-in-out"),
        )

        st.plotly_chart(
            heat_fig,
            use_container_width=True,
            config={
                "displayModeBar": True, "displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 2},
            },
        )

        render_section_export(
            base_name=f"TrustIntel_{display_name}_Platform_Matrix",
            data=comparison,
            figure=heat_fig,
            sheet_name="Platform Matrix",
        )


# ---------------------------
# Language spread
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Multilingual spread</div>',
    unsafe_allow_html=True,
)
st.subheader("Which languages are appearing on which platforms?")

if language_platform.empty:
    st.info(
        "No multilingual platform distribution is available."
    )
else:
    pivot = language_platform.pivot(
        index="Language",
        columns="Platform",
        values="Mentions",
    ).fillna(0)

    lang_heat = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            colorscale=MIXED_SCALE,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Platform: %{x}<br>"
                "Mentions: %{z:.0f}"
                "<extra></extra>"
            ),
        )
    )

    lang_heat.update_layout(
        height=max(
            390,
            56 * len(pivot.index),
        ),
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=55,
        ),
        xaxis=dict(
            title="Platform",
        ),
        yaxis=dict(
            title="Language",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        transition=dict(duration=450, easing="cubic-in-out"),
    )

    st.plotly_chart(
        lang_heat,
        use_container_width=True,
        config={
            "displayModeBar": True, "displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 2},
        },
    )

    render_section_export(
        base_name=f"TrustIntel_{display_name}_Language_Platform",
        data=language_platform,
        figure=lang_heat,
        sheet_name="Language x Platform",
    )


# ---------------------------
# Narrative pressure landscape
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Narrative pressure</div>',
    unsafe_allow_html=True,
)
st.subheader("How do engagement and sentiment combine into risk?")

plot_posts = risk_posts.copy()

max_engagement = max(
    float(
        plot_posts[
            "Engagement"
        ]
        .fillna(0)
        .max()
    ),
    1.0,
)

bubble_sizes = (
    12
    + 28
    * (
        plot_posts[
            "Engagement"
        ]
        .fillna(0)
        / max_engagement
    )
)

pressure_fig = go.Figure(
    go.Scatter(
        x=plot_posts[
            "Sentiment"
        ],
        y=plot_posts[
            "Risk Signal"
        ],
        mode="markers",
        marker=dict(
            size=bubble_sizes,
            color=plot_posts["Risk Signal"],
            colorscale=RISK_SCALE,
            cmin=0,
            cmax=100,
            showscale=True,
            colorbar=dict(
                title="Risk",
                thickness=12,
            ),
            opacity=.74,
            line=dict(
                width=.7,
                color="white",
            ),
        ),
        text=plot_posts[
            "Title"
        ],
        customdata=plot_posts[
            [
                "Platform",
                "Language",
                "Engagement",
                "Author",
            ]
        ],
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Platform: %{customdata[0]}<br>"
            "Language: %{customdata[1]}<br>"
            "Engagement: %{customdata[2]}<br>"
            "Author: %{customdata[3]}<br>"
            "Sentiment: %{x:.3f}<br>"
            "Risk Signal: %{y:.1f}"
            "<extra></extra>"
        ),
    )
)

pressure_fig.add_hline(
    y=60,
    line_dash="dash",
    opacity=.35,
)

pressure_fig.add_vline(
    x=0,
    line_dash="dot",
    opacity=.25,
)

pressure_fig.update_layout(
    height=500,
    margin=dict(
        l=20,
        r=20,
        t=20,
        b=35,
    ),
    xaxis=dict(
        title="Sentiment ← negative | positive →",
        range=[-1, 1],
        showgrid=True,
        zeroline=False,
    ),
    yaxis=dict(
        title="Narrative Risk Signal",
        range=[0, 100],
        showgrid=True,
        zeroline=False,
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    showlegend=False,
    transition=dict(duration=500, easing="cubic-in-out"),
)

st.plotly_chart(
    pressure_fig,
    use_container_width=True,
    config={
        "displayModeBar": True, "displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 2},
    },
)

render_section_export(
    base_name=f"TrustIntel_{display_name}_Narrative_Pressure",
    data=plot_posts,
    figure=pressure_fig,
    sheet_name="Narrative Pressure",
)


# ---------------------------
# Cross-platform overlap
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Cross-platform overlap</div>',
    unsafe_allow_html=True,
)
st.subheader("Which terms are recurring across platforms?")

if overlap.empty:
    st.info(
        "No recurring terms appeared on multiple platforms "
        "in the current evidence set."
    )
else:
    overlap_plot = (
        overlap.sort_values(
            [
                "Platform Count",
                "Frequency",
            ],
            ascending=True,
        )
        .tail(15)
    )

    overlap_fig = go.Figure(
        go.Bar(
            x=overlap_plot[
                "Frequency"
            ],
            y=overlap_plot[
                "Term"
            ],
            orientation="h",
            text=overlap_plot[
                "Platform Count"
            ].astype(str)
            + " platforms",
            textposition="outside",
            marker=dict(
                color=overlap_plot["Platform Count"],
                colorscale=MIXED_SCALE,
                line=dict(color="white", width=1),
            ),
            customdata=overlap_plot[
                [
                    "Platforms",
                    "Platform Count",
                ]
            ],
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Frequency: %{x}<br>"
                "Platforms: %{customdata[0]}<br>"
                "Platform Count: %{customdata[1]}"
                "<extra></extra>"
            ),
        )
    )

    overlap_fig.update_layout(
        height=max(
            380,
            42 * len(overlap_plot),
        ),
        margin=dict(
            l=10,
            r=80,
            t=10,
            b=25,
        ),
        xaxis=dict(
            title="Cross-platform frequency",
            showgrid=True,
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
        overlap_fig,
        use_container_width=True,
        config={
            "displayModeBar": True, "displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 2},
        },
    )

    render_section_export(
        base_name=f"TrustIntel_{display_name}_Cross_Platform_Overlap",
        data=overlap_plot,
        figure=overlap_fig,
        sheet_name="Cross Platform Overlap",
    )


# ---------------------------
# Priority queue
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Priority narratives</div>',
    unsafe_allow_html=True,
)
st.subheader("What requires attention now?")

priority_posts = (
    risk_posts.sort_values(
        "Risk Signal",
        ascending=False,
    )
    .copy()
)

priority_posts[
    "Priority"
] = priority_posts[
    "Risk Signal"
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

priority_columns = [
    "Priority",
    "Platform",
    "Title",
    "Language",
    "Engagement",
    "Sentiment",
    "Risk Signal",
    "Url",
]

st.dataframe(
    priority_posts[
        [
            column
            for column in priority_columns
            if column in priority_posts.columns
        ]
    ].head(15),
    use_container_width=True,
    hide_index=True,
)

render_section_export(
    base_name=f"TrustIntel_{display_name}_Omnichannel_Priority_Narratives",
    data=priority_posts[
        [
            column
            for column in priority_columns
            if column in priority_posts.columns
        ]
    ],
    sheet_name="Priority Narratives",
)


# ---------------------------
# Audit sections
# ---------------------------
with st.expander(
    "Source coverage and connector readiness"
):
    st.dataframe(
        coverage,
        use_container_width=True,
        hide_index=True,
    )

    if errors:
        st.write("Source connection notes")
        for error in sorted(
            set(errors)
        ):
            st.write(error)

with st.expander(
    "Full platform comparison metrics"
):
    st.dataframe(
        comparison,
        use_container_width=True,
        hide_index=True,
    )

with st.expander(
    "Full multilingual social evidence"
):
    columns = [
        "Platform",
        "Title",
        "Author",
        "Published_At",
        "Language",
        "Search Language",
        "Search Query Used",
        "Engagement",
        "Sentiment",
        "Sentiment_Label",
        "Sentiment Method",
        "Sentiment Confidence",
        "Risk Signal",
        "Url",
    ]

    st.dataframe(
        priority_posts[
            [
                column
                for column in columns
                if column in priority_posts.columns
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

with st.expander(
    "Methodology and connector limitations"
):
    st.info(
        "This module uses live public or approved sources where access "
        "is available. Some platforms require official API credentials "
        "or approved permissions and therefore remain connector-ready "
        "rather than live. Multilingual sentiment outside English uses "
        "lightweight prototype lexicons that require further validation. "
        "Risk Signal and Platform Risk are comparative prototype indicators "
        "for decision support, not automated determinations of harm."
    )
