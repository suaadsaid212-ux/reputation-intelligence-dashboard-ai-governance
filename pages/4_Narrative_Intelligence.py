from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.chart_theme import (
    MIXED_SCALE,
    PALETTE,
    RISK_SCALE,
    categorical_colors,
)
from utils.excel_export import dataframes_to_excel_bytes
from utils.entity_selector import (
    get_entity,
    get_entity_query,
)
from utils.live_ops import (
    render_live_status,
    source_health_frame,
)
from utils.multilingual_content import (
    fetch_multilingual_news,
    get_selected_content_languages,
)
from utils.narrative_fusion import (
    cluster_narratives,
    deduplicate_records,
    discover_rss_feeds,
    fetch_gdelt_articles,
    fetch_rss_articles,
    normalize_google_news,
    retrieval_timestamp,
)


st.set_page_config(
    page_title="Narrative Source Fusion",
    page_icon="🧠",
    layout="wide",
)

entity = get_entity()

entity_name = entity["Entity_Name"]
display_name = entity["Short_Name"]

query = (
    get_entity_query(
        entity,
        "News_Query",
    )
    or display_name
)

website = str(
    entity.get(
        "Website",
        "",
    )
).strip()

content_languages = (
    get_selected_content_languages()
)

st.title(
    "Narrative Source Fusion"
)

st.caption(
    f"{display_name} • {entity['Country']} • {entity['Sector']} • "
    "Multi-source narrative collection, deduplication and corroboration"
)


source_options = [
    "Google News",
    "GDELT",
    "Official / Public RSS",
]

selected_sources = st.sidebar.multiselect(
    "Narrative sources",
    source_options,
    default=[
        "Google News",
        "GDELT",
    ],
)

window_label = st.sidebar.selectbox(
    "Evidence window",
    [
        "24 Hours",
        "7 Days",
        "30 Days",
        "90 Days",
    ],
    index=1,
)

depth_label = st.sidebar.selectbox(
    "Research depth",
    [
        "Standard",
        "Deep",
        "Maximum",
    ],
    index=1,
    help=(
        "Standard is suitable for quick monitoring. Deep requests substantially "
        "more evidence. Maximum is intended for research/export and may load more slowly."
    ),
)

DEPTH_SETTINGS = {
    "Standard": {
        "google_limit": 15,
        "gdelt_limit": 150,
        "rss_limit": 30,
    },
    "Deep": {
        "google_limit": 30,
        "gdelt_limit": 250,
        "rss_limit": 50,
    },
    "Maximum": {
        "google_limit": 50,
        "gdelt_limit": 250,
        "rss_limit": 75,
    },
}

depth_settings = DEPTH_SETTINGS[
    depth_label
]

google_limit = depth_settings[
    "google_limit"
]

gdelt_limit = depth_settings[
    "gdelt_limit"
]

rss_limit = depth_settings[
    "rss_limit"
]

expand_gdelt = st.sidebar.checkbox(
    "Expand GDELT topical queries",
    value=(
        depth_label != "Standard"
    ),
    help=(
        "Adds carefully bounded topical lenses such as reputation, governance, "
        "risk and AI to increase external evidence depth. Results are deduplicated."
    ),
)

gdelt_lenses = st.sidebar.multiselect(
    "GDELT topical lenses",
    [
        "reputation",
        "governance",
        "risk",
        "crisis",
        "trust",
        "AI",
    ],
    default=[
        "reputation",
        "governance",
        "risk",
    ],
    disabled=not expand_gdelt,
)

cluster_threshold = st.sidebar.slider(
    "Narrative clustering similarity",
    min_value=0.15,
    max_value=0.60,
    value=0.28,
    step=0.01,
    help=(
        "Higher values require more title-word overlap. "
        "Clustering is language-sensitive and remains a prototype."
    ),
)

manual_rss = st.sidebar.text_area(
    "Additional RSS / Atom feed URLs",
    "",
    help=(
        "Optional. Enter one public feed URL per line. "
        "TrustIntel will also try to discover RSS/Atom feeds "
        "from the selected organization's website."
    ),
)


status_rows = []

if "Google News" in selected_sources:
    status_rows.append(
        (
            "Google News",
            "LIVE",
        )
    )

if "GDELT" in selected_sources:
    status_rows.append(
        (
            "GDELT",
            "ON-DEMAND",
        )
    )

if "Official / Public RSS" in selected_sources:
    status_rows.append(
        (
            "RSS",
            "ON-DEMAND",
        )
    )

status_rows.append(
    (
        "Fusion scoring",
        "PROTOTYPE",
    )
)

render_live_status(
    status_rows,
    note=(
        "TrustIntel now separates the collection source from the analytical layer. "
        "Narrative clusters, cross-source confidence and Narrative Risk are "
        "prototype decision-support indicators rather than generated facts."
    ),
)


if not selected_sources:
    st.warning(
        "Select at least one narrative source."
    )
    st.stop()


window_to_gdelt = {
    "24 Hours": "24h",
    "7 Days": "7d",
    "30 Days": "30d",
    "90 Days": "90d",
}

window_to_delta = {
    "24 Hours": timedelta(
        hours=24
    ),
    "7 Days": timedelta(
        days=7
    ),
    "30 Days": timedelta(
        days=30
    ),
    "90 Days": timedelta(
        days=90
    ),
}


@st.cache_data(
    ttl=900,
    show_spinner=False,
)
def load_google(
    query,
    languages,
    limit_per_language,
):
    frame = fetch_multilingual_news(
        query=query,
        languages=list(
            languages
        ),
        limit_per_language=int(
            limit_per_language
        ),
    )

    return (
        normalize_google_news(
            frame
        ),
        retrieval_timestamp(),
    )


@st.cache_data(
    ttl=900,
    show_spinner=False,
)
def load_gdelt(
    query,
    timespan,
    max_records,
):
    frame, error = (
        fetch_gdelt_articles(
            query,
            timespan=timespan,
            max_records=max_records,
        )
    )

    return (
        frame,
        error,
        retrieval_timestamp(),
    )


@st.cache_data(
    ttl=3600,
    show_spinner=False,
)
def find_rss(
    website,
):
    return discover_rss_feeds(
        website
    )


@st.cache_data(
    ttl=900,
    show_spinner=False,
)
def load_rss(
    feed_urls,
    query,
    official_domain,
    limit_per_feed,
):
    frame, notes = fetch_rss_articles(
        list(
            feed_urls
        ),
        query=query,
        official_domain=official_domain,
        limit_per_feed=int(
            limit_per_feed
        ),
    )

    return (
        frame,
        notes,
        retrieval_timestamp(),
    )


refresh_col, info_col = st.columns(
    [
        1,
        4,
    ]
)

with refresh_col:
    if st.button(
        "↻ Refresh Sources",
        use_container_width=True,
    ):
        load_google.clear()
        load_gdelt.clear()
        find_rss.clear()
        load_rss.clear()
        st.rerun()

with info_col:
    st.caption(
        f"Monitoring query: {query} • "
        f"Window: {window_label} • "
        f"Research depth: {depth_label} • "
        f"Data languages selected: {len(content_languages)}"
    )


frames = []
source_notes = []
retrieval_times = []
rss_urls = []
rss_discovery_error = ""


with st.spinner(
    "Fusing multi-source narrative evidence..."
):
    if "Google News" in selected_sources:
        try:
            google_df, retrieved = (
                load_google(
                    query,
                    tuple(
                        content_languages
                    ),
                    google_limit,
                )
            )

            if not google_df.empty:
                frames.append(
                    google_df
                )

            retrieval_times.append(
                retrieved
            )
        except Exception as error:
            source_notes.append(
                f"Google News: {error}"
            )

    if "GDELT" in selected_sources:
        gdelt_queries = [
            query
        ]

        if expand_gdelt:
            for lens in gdelt_lenses:
                expanded_query = (
                    f'("{query}") {lens}'
                )

                if expanded_query not in gdelt_queries:
                    gdelt_queries.append(
                        expanded_query
                    )

        gdelt_frames = []

        for current_gdelt_query in gdelt_queries:
            gdelt_df, gdelt_error, retrieved = (
                load_gdelt(
                    current_gdelt_query,
                    window_to_gdelt[
                        window_label
                    ],
                    gdelt_limit,
                )
            )

            if not gdelt_df.empty:
                gdelt_df = gdelt_df.copy()
                gdelt_df[
                    "Collection Query"
                ] = current_gdelt_query
                gdelt_frames.append(
                    gdelt_df
                )

            if gdelt_error:
                source_notes.append(
                    f"GDELT ({current_gdelt_query}): {gdelt_error}"
                )

            retrieval_times.append(
                retrieved
            )

        if gdelt_frames:
            frames.append(
                pd.concat(
                    gdelt_frames,
                    ignore_index=True,
                )
            )

    if "Official / Public RSS" in selected_sources:
        if website:
            discovered, rss_discovery_error = (
                find_rss(
                    website
                )
            )
            rss_urls.extend(
                discovered
            )

        manual_urls = [
            line.strip()
            for line in manual_rss.splitlines()
            if line.strip()
        ]

        for url in manual_urls:
            if url not in rss_urls:
                rss_urls.append(
                    url
                )

        official_domain = ""

        try:
            official_domain = (
                urlparse(
                    website
                )
                .netloc
                .lower()
                .replace(
                    "www.",
                    "",
                )
            )
        except Exception:
            official_domain = ""

        if rss_urls:
            rss_df, rss_notes, retrieved = (
                load_rss(
                    tuple(
                        rss_urls
                    ),
                    query,
                    official_domain,
                    rss_limit,
                )
            )

            if not rss_df.empty:
                frames.append(
                    rss_df
                )

            source_notes.extend(
                rss_notes
            )
            retrieval_times.append(
                retrieved
            )
        elif rss_discovery_error:
            source_notes.append(
                "RSS discovery: "
                + rss_discovery_error
            )


if not frames:
    st.error(
        "No narrative evidence was returned from the selected sources."
    )

    if source_notes:
        with st.expander(
            "Source connection notes",
            expanded=True,
        ):
            for note in source_notes:
                st.write(
                    note
                )

    st.stop()


fusion_df = pd.concat(
    frames,
    ignore_index=True,
)

raw_record_count = int(
    len(
        fusion_df
    )
)

fusion_df = deduplicate_records(
    fusion_df
)

deduplicated_record_count = int(
    len(
        fusion_df
    )
)


fusion_df[
    "Published Parsed"
] = pd.to_datetime(
    fusion_df[
        "Published"
    ],
    errors="coerce",
    utc=True,
)

cutoff = (
    datetime.now(
        timezone.utc
    )
    - window_to_delta[
        window_label
    ]
)

has_parsed_date = (
    fusion_df[
        "Published Parsed"
    ].notna()
)

fusion_df = fusion_df[
    (
        ~has_parsed_date
    )
    | fusion_df[
        "Published Parsed"
    ].ge(
        cutoff
    )
].copy()


if fusion_df.empty:
    st.warning(
        "Sources returned evidence, but no records remained inside the selected evidence window."
    )
    st.stop()


fusion_df, clusters_df = (
    cluster_narratives(
        fusion_df,
        similarity_threshold=cluster_threshold,
    )
)


if clusters_df.empty:
    st.warning(
        "No narrative clusters could be produced from the current evidence."
    )
    st.stop()


source_type_count = int(
    fusion_df[
        "Source Type"
    ].nunique()
)

source_class_count = int(
    fusion_df[
        "Source Class"
    ].nunique()
)

language_count = int(
    fusion_df[
        "Language"
    ].nunique()
)

cross_source_clusters = int(
    clusters_df[
        "Source Diversity"
    ]
    .ge(
        2
    )
    .sum()
)

high_conf_clusters = int(
    clusters_df[
        "Cross-Source Confidence"
    ]
    .eq(
        "High"
    )
    .sum()
)

top_cluster = (
    clusters_df.iloc[0]
)

top_cluster_label = str(
    top_cluster[
        "Narrative Cluster"
    ]
)

if len(
    top_cluster_label
) > 100:
    top_cluster_label = (
        top_cluster_label[
            :97
        ]
        + "..."
    )


st.markdown(
    '<div class="ti-section-label">Fusion status</div>',
    unsafe_allow_html=True,
)

k1, k2, k3, k4, k5, k6 = st.columns(
    6
)

k1.metric(
    "Raw Records",
    raw_record_count,
)

k2.metric(
    "Unique Evidence",
    deduplicated_record_count,
)

k3.metric(
    "Source Types",
    source_type_count,
)

k4.metric(
    "Narrative Clusters",
    len(
        clusters_df
    ),
)

k5.metric(
    "Cross-Source Clusters",
    cross_source_clusters,
)

k6.metric(
    "Languages",
    language_count,
)


brief = (
    f"TrustIntel collected <strong>{raw_record_count}</strong> raw records and retained "
    f"<strong>{deduplicated_record_count}</strong> unique evidence records after deduplication. "
    f"from <strong>{source_type_count}</strong> active source type(s) and "
    f"organized them into <strong>{len(clusters_df)}</strong> narrative cluster(s). "
    f"<strong>{cross_source_clusters}</strong> cluster(s) appear across at least "
    f"two collection source types, while <strong>{high_conf_clusters}</strong> "
    f"currently have high cross-source diversity. The highest-priority current "
    f"cluster is <strong>{top_cluster_label}</strong>."
)

st.markdown(
    f"""
    <div class="ti-brief">
        <div class="ti-brief-kicker">Narrative Fusion Brief</div>
        <div class="ti-brief-text">{brief}</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------
# Source mix + corroboration
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Source architecture</div>',
    unsafe_allow_html=True,
)
st.subheader(
    "Which sources are contributing to the intelligence picture?"
)

source_left, source_right = st.columns(
    2
)

with source_left:
    source_mix = (
        fusion_df[
            "Source Type"
        ]
        .value_counts()
        .rename_axis(
            "Source Type"
        )
        .reset_index(
            name="Records"
        )
    )

    source_fig = go.Figure(
        go.Pie(
            labels=source_mix[
                "Source Type"
            ],
            values=source_mix[
                "Records"
            ],
            hole=.58,
            marker=dict(
                colors=categorical_colors(
                    len(
                        source_mix
                    )
                ),
            ),
            textinfo="label+percent",
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Evidence records: %{value}<br>"
                "Share: %{percent}"
                "<extra></extra>"
            ),
        )
    )

    source_fig.update_layout(
        height=390,
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        transition=dict(
            duration=450,
            easing="cubic-in-out",
        ),
    )

    st.plotly_chart(
        source_fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
        },
    )


with source_right:
    source_language = (
        fusion_df.groupby(
            [
                "Source Type",
                "Language",
            ]
        )
        .size()
        .reset_index(
            name="Records"
        )
    )

    source_language_pivot = (
        source_language.pivot(
            index="Source Type",
            columns="Language",
            values="Records",
        )
        .fillna(
            0
        )
    )

    heat_fig = go.Figure(
        go.Heatmap(
            z=source_language_pivot.values,
            x=source_language_pivot.columns.tolist(),
            y=source_language_pivot.index.tolist(),
            colorscale=MIXED_SCALE,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Language: %{x}<br>"
                "Evidence records: %{z:.0f}"
                "<extra></extra>"
            ),
        )
    )

    heat_fig.update_layout(
        height=390,
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=45,
        ),
        xaxis=dict(
            title="Language",
        ),
        yaxis=dict(
            title="",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        transition=dict(
            duration=450,
            easing="cubic-in-out",
        ),
    )

    st.plotly_chart(
        heat_fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
        },
    )


# ---------------------------
# Narrative clusters
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Narrative clusters</div>',
    unsafe_allow_html=True,
)
st.subheader(
    "Which narratives are gaining cross-source support?"
)

top_clusters = (
    clusters_df.head(
        15
    )
    .sort_values(
        "Narrative Risk",
        ascending=True,
    )
)

cluster_fig = go.Figure(
    go.Bar(
        x=top_clusters[
            "Narrative Risk"
        ],
        y=top_clusters[
            "Narrative Cluster"
        ],
        orientation="h",
        text=top_clusters[
            "Narrative Risk"
        ],
        textposition="outside",
        marker=dict(
            color=top_clusters[
                "Narrative Risk"
            ],
            colorscale=RISK_SCALE,
            cmin=0,
            cmax=100,
            line=dict(
                color="white",
                width=1,
            ),
        ),
        customdata=top_clusters[
            [
                "Records",
                "Source Diversity",
                "Cross-Source Confidence",
                "Negative Share %",
            ]
        ],
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Narrative Risk: %{x:.1f}<br>"
            "Records: %{customdata[0]}<br>"
            "Source types: %{customdata[1]}<br>"
            "Cross-source confidence: %{customdata[2]}<br>"
            "Negative share: %{customdata[3]:.1f}%"
            "<extra></extra>"
        ),
    )
)

cluster_fig.update_layout(
    height=max(
        430,
        44
        * len(
            top_clusters
        ),
    ),
    margin=dict(
        l=10,
        r=55,
        t=10,
        b=30,
    ),
    xaxis=dict(
        title="Narrative Risk",
        range=[
            0,
            100,
        ],
        showgrid=True,
        zeroline=False,
    ),
    yaxis=dict(
        title="",
        automargin=True,
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    showlegend=False,
    transition=dict(
        duration=500,
        easing="cubic-in-out",
    ),
)

st.plotly_chart(
    cluster_fig,
    use_container_width=True,
    config={
        "displayModeBar": False,
    },
)


# ---------------------------
# Corroboration landscape
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Corroboration landscape</div>',
    unsafe_allow_html=True,
)
st.subheader(
    "How broad is each narrative across independent collection sources?"
)

bubble = go.Figure(
    go.Scatter(
        x=clusters_df[
            "Source Diversity"
        ],
        y=clusters_df[
            "Records"
        ],
        mode="markers",
        marker=dict(
            size=(
                14
                + 34
                * (
                    clusters_df[
                        "Narrative Risk"
                    ]
                    / 100
                )
            ),
            color=clusters_df[
                "Narrative Risk"
            ],
            colorscale=RISK_SCALE,
            cmin=0,
            cmax=100,
            showscale=True,
            colorbar=dict(
                title="Risk",
                thickness=12,
            ),
            opacity=.76,
            line=dict(
                color="white",
                width=.8,
            ),
        ),
        text=clusters_df[
            "Narrative Cluster"
        ],
        customdata=clusters_df[
            [
                "Cross-Source Confidence",
                "Publisher Diversity",
                "Language",
                "Negative Share %",
            ]
        ],
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Source types: %{x}<br>"
            "Evidence records: %{y}<br>"
            "Cross-source confidence: %{customdata[0]}<br>"
            "Publishers: %{customdata[1]}<br>"
            "Language: %{customdata[2]}<br>"
            "Negative share: %{customdata[3]:.1f}%"
            "<extra></extra>"
        ),
    )
)

bubble.update_layout(
    height=480,
    margin=dict(
        l=20,
        r=20,
        t=15,
        b=35,
    ),
    xaxis=dict(
        title="Collection Source Diversity",
        dtick=1,
        rangemode="tozero",
        showgrid=True,
        zeroline=False,
    ),
    yaxis=dict(
        title="Evidence Records in Cluster",
        rangemode="tozero",
        showgrid=True,
        zeroline=False,
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    showlegend=False,
    transition=dict(
        duration=500,
        easing="cubic-in-out",
    ),
)

st.plotly_chart(
    bubble,
    use_container_width=True,
    config={
        "displayModeBar": False,
    },
)


# ---------------------------
# Cluster table
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Decision view</div>',
    unsafe_allow_html=True,
)
st.subheader(
    "Priority narrative clusters"
)

cluster_display = clusters_df[
    [
        "Cluster ID",
        "Narrative Cluster",
        "Language",
        "Records",
        "Source Types",
        "Source Diversity",
        "Publisher Diversity",
        "Cross-Source Confidence",
        "Average Sentiment",
        "Negative Share %",
        "Narrative Risk",
    ]
].copy()

st.dataframe(
    cluster_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Narrative Risk":
            st.column_config.ProgressColumn(
                "Narrative Risk",
                min_value=0,
                max_value=100,
                format="%.1f",
            )
    },
)


# ---------------------------
# Evidence stream
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Evidence stream</div>',
    unsafe_allow_html=True,
)
st.subheader(
    "Evidence behind the narrative clusters"
)

evidence_display = fusion_df.copy()

evidence_display[
    "Narrative Risk"
] = evidence_display[
    "Cluster ID"
].map(
    clusters_df.set_index(
        "Cluster ID"
    )[
        "Narrative Risk"
    ]
)

evidence_display = evidence_display.sort_values(
    [
        "Narrative Risk",
        "Published Parsed",
    ],
    ascending=[
        False,
        False,
    ],
    na_position="last",
)

display_columns = [
    "Cluster ID",
    "Headline",
    "Source Type",
    "Source Class",
    "Source Name",
    "Language",
    "Source Country",
    "Edition Country",
    "Sentiment",
    "Sentiment Label",
    "Narrative Risk",
    "Published",
    "Link",
]

st.dataframe(
    evidence_display[
        [
            column
            for column in display_columns
            if column
            in evidence_display.columns
        ]
    ].head(
        100
    ),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Narrative Risk":
            st.column_config.ProgressColumn(
                "Narrative Risk",
                min_value=0,
                max_value=100,
                format="%.1f",
            ),
        "Link":
            st.column_config.LinkColumn(
                "Evidence Link",
                display_text="Open",
            ),
    },
)



# ---------------------------
# Research export
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Research export</div>',
    unsafe_allow_html=True,
)
st.subheader(
    "Download the full underlying dataset"
)

source_summary_export = (
    fusion_df[
        "Source Type"
    ]
    .value_counts()
    .rename_axis(
        "Source Type"
    )
    .reset_index(
        name="Evidence Records"
    )
)

language_summary_export = (
    fusion_df.groupby(
        "Language"
    )
    .agg(
        Evidence_Records=(
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
                values.lt(
                    -0.05
                )
                .mean()
                * 100
            ),
        ),
        Source_Types=(
            "Source Type",
            "nunique",
        ),
    )
    .reset_index()
)

source_language_export = (
    fusion_df.groupby(
        [
            "Source Type",
            "Language",
        ]
    )
    .size()
    .reset_index(
        name="Evidence Records"
    )
)

metadata = {
    "Entity": display_name,
    "Entity Name": entity_name,
    "Home Country": entity.get(
        "Country",
        "",
    ),
    "Sector": entity.get(
        "Sector",
        "",
    ),
    "Monitoring Query": query,
    "Evidence Window": window_label,
    "Research Depth": depth_label,
    "Selected Sources": ", ".join(
        selected_sources
    ),
    "Selected Languages": len(
        content_languages
    ),
    "Raw Records": raw_record_count,
    "Unique Evidence": deduplicated_record_count,
    "Narrative Clusters": len(
        clusters_df
    ),
    "Cross-Source Clusters": cross_source_clusters,
    "Cluster Similarity Threshold": cluster_threshold,
    "Export Note": (
        "Narrative Risk and cross-source confidence are prototype "
        "decision-support indicators. Evidence links are preserved."
    ),
}

excel_bytes = dataframes_to_excel_bytes(
    [
        (
            "Evidence",
            evidence_display.drop(
                columns=[
                    "Canonical Title",
                    "Canonical URL",
                    "Published Parsed",
                ],
                errors="ignore",
            ),
        ),
        (
            "Narrative Clusters",
            clusters_df,
        ),
        (
            "Source Summary",
            source_summary_export,
        ),
        (
            "Language Summary",
            language_summary_export,
        ),
        (
            "Source x Language",
            source_language_export,
        ),
    ],
    metadata=metadata,
)

download_left, download_right = st.columns(
    2
)

with download_left:
    st.download_button(
        "⬇ Download Full Research Workbook (.xlsx)",
        data=excel_bytes,
        file_name=(
            f"TrustIntel_{display_name}_Narrative_Research.xlsx"
        ),
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        use_container_width=True,
    )

with download_right:
    csv_bytes = (
        evidence_display.drop(
            columns=[
                "Published Parsed",
            ],
            errors="ignore",
        )
        .to_csv(
            index=False
        )
        .encode(
            "utf-8-sig"
        )
    )

    st.download_button(
        "⬇ Download Raw Evidence (.csv)",
        data=csv_bytes,
        file_name=(
            f"TrustIntel_{display_name}_Narrative_Evidence.csv"
        ),
        mime="text/csv",
        use_container_width=True,
    )

st.caption(
    "The Excel workbook contains the full evidence dataset plus cluster, "
    "source, language and metadata sheets. It is not limited to the rows "
    "currently visible on screen."
)

st.session_state[
    "ti_research_evidence"
] = evidence_display.copy()

st.session_state[
    "ti_research_clusters"
] = clusters_df.copy()

st.session_state[
    "ti_research_metadata"
] = metadata.copy()


# ---------------------------
# Source health
# ---------------------------
with st.expander(
    "Source health, feeds and connection notes"
):
    health_rows = []

    for source_name in source_options:
        selected = (
            source_name
            in selected_sources
        )

        if source_name == "Google News":
            health_rows.append(
                [
                    source_name,
                    (
                        "LIVE + cache"
                        if selected
                        else "Not selected"
                    ),
                    "15 minute page cache",
                    "Selected global data languages",
                    (
                        "Google News RSS editions."
                    ),
                ]
            )

        elif source_name == "GDELT":
            health_rows.append(
                [
                    source_name,
                    (
                        "ON-DEMAND"
                        if selected
                        else "Not selected"
                    ),
                    "Queried when page runs",
                    "Global external news corpus",
                    (
                        "GDELT DOC 2.0 article search."
                    ),
                ]
            )

        else:
            health_rows.append(
                [
                    source_name,
                    (
                        "ON-DEMAND"
                        if selected
                        else "Not selected"
                    ),
                    "Queried when page runs",
                    "Discovered / manually supplied feeds",
                    (
                        f"{len(rss_urls)} feed(s) available in this run."
                    ),
                ]
            )

    st.dataframe(
        source_health_frame(
            health_rows
        ),
        use_container_width=True,
        hide_index=True,
    )

    if rss_urls:
        st.write(
            "**RSS / Atom feeds used or discovered:**"
        )

        for feed_url in rss_urls:
            st.write(
                feed_url
            )

    if source_notes:
        st.write(
            "**Connection notes:**"
        )

        for note in source_notes:
            st.write(
                note
            )


with st.expander(
    "Narrative Fusion methodology and limitations"
):
    st.write(
        "TrustIntel does not generate the underlying narratives. "
        "It collects public evidence, normalizes records, groups similar titles "
        "and computes comparative decision-support indicators."
    )

    st.write(
        "Current narrative clustering uses language-sensitive lexical overlap. "
        "It is intentionally transparent and lightweight, but it will not reliably "
        "merge semantically equivalent narratives written in different languages. "
        "A production version should use validated multilingual embeddings and "
        "human-reviewed cluster evaluation."
    )

    st.write(
        "Cross-Source Confidence reflects collection-source diversity, not truth. "
        "The same inaccurate claim can be repeated by multiple sources. "
        "Truth assessment belongs in the separate Trust & Verification Console."
    )

    st.write(
        "Narrative Risk combines negative share, cluster volume, source diversity "
        "and negative sentiment. It is a prototype prioritization score, not an "
        "automated determination of harm."
    )
