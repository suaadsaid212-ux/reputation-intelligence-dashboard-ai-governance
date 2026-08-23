from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.chart_theme import (
    MIXED_SCALE,
    RISK_SCALE,
    categorical_colors,
)
from utils.excel_export import (
    dataframes_to_excel_bytes,
)
from utils.section_export import render_section_export
from utils.registry_utils import load_registry
from utils.live_ops import (
    render_live_status,
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
    page_title="Research Dataset & Export",
    page_icon="🧪",
    layout="wide",
)

st.title(
    "Research Dataset & Export"
)

st.caption(
    "Build a larger multi-organization evidence corpus for analysis, "
    "research, validation and Excel export."
)

render_live_status(
    [
        ("Google News", "LIVE"),
        ("GDELT", "ON-DEMAND"),
        ("Public RSS", "ON-DEMAND"),
        ("Dataset analytics", "PROTOTYPE"),
    ],
    note=(
        "This workspace is designed for evidence depth rather than a small executive snapshot. "
        "Requested record counts are targets, not guarantees; public sources may return fewer "
        "matching records for some entities or languages."
    ),
)


try:
    registry_df = load_registry()
except FileNotFoundError:
    st.error(
        "Registry file not found: config/entity_registry.csv"
    )
    st.stop()


content_languages = (
    get_selected_content_languages()
)

entity_options = (
    registry_df[
        "Entity_Name"
    ]
    .dropna()
    .astype(str)
    .tolist()
)

selected_entities = st.sidebar.multiselect(
    "Organizations",
    entity_options,
    default=entity_options[:2],
    max_selections=5,
    help=(
        "For deep research, start with 1–3 organizations. "
        "Five organizations with Maximum depth can take substantially longer."
    ),
)

source_options = [
    "Google News",
    "GDELT",
    "Official / Public RSS",
]

selected_sources = st.sidebar.multiselect(
    "Evidence sources",
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
    index=2,
)

depth_label = st.sidebar.selectbox(
    "Dataset depth",
    [
        "Standard",
        "Deep",
        "Maximum",
    ],
    index=1,
)

DEPTH_SETTINGS = {
    "Standard": {
        "google_limit": 15,
        "gdelt_limit": 150,
        "rss_limit": 30,
        "lenses": [
            "reputation",
        ],
    },
    "Deep": {
        "google_limit": 30,
        "gdelt_limit": 250,
        "rss_limit": 50,
        "lenses": [
            "reputation",
            "governance",
            "risk",
        ],
    },
    "Maximum": {
        "google_limit": 50,
        "gdelt_limit": 250,
        "rss_limit": 75,
        "lenses": [
            "reputation",
            "governance",
            "risk",
            "crisis",
            "trust",
            "AI",
        ],
    },
}

settings = DEPTH_SETTINGS[
    depth_label
]

cluster_threshold = st.sidebar.slider(
    "Cluster similarity",
    min_value=.15,
    max_value=.60,
    value=.28,
    step=.01,
)

include_expanded_queries = st.sidebar.checkbox(
    "Use topical GDELT query expansion",
    value=True,
)

if not selected_entities:
    st.warning(
        "Select at least one organization."
    )
    st.stop()

if not selected_sources:
    st.warning(
        "Select at least one evidence source."
    )
    st.stop()

if (
    depth_label == "Maximum"
    and len(selected_entities) > 2
):
    st.warning(
        "Maximum depth is intentionally limited to two organizations per run "
        "to keep the public-source requests and clustering workload manageable. "
        "Select two organizations or switch to Deep depth."
    )
    st.stop()

if (
    depth_label == "Deep"
    and len(selected_entities) > 3
):
    st.info(
        "Deep depth across more than three organizations may take noticeably longer. "
        "For the cleanest research run, use 1–3 organizations at a time."
    )


window_to_gdelt = {
    "24 Hours": "24h",
    "7 Days": "7d",
    "30 Days": "30d",
    "90 Days": "90d",
}

window_to_delta = {
    "24 Hours": timedelta(hours=24),
    "7 Days": timedelta(days=7),
    "30 Days": timedelta(days=30),
    "90 Days": timedelta(days=90),
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
        languages=list(languages),
        limit_per_language=int(limit_per_language),
    )

    return (
        normalize_google_news(frame),
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
    frame, error = fetch_gdelt_articles(
        query,
        timespan=timespan,
        max_records=max_records,
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
        list(feed_urls),
        query=query,
        official_domain=official_domain,
        limit_per_feed=int(limit_per_feed),
    )

    return (
        frame,
        notes,
        retrieval_timestamp(),
    )


toolbar_left, toolbar_right = st.columns(
    [
        1,
        4,
    ]
)

with toolbar_left:
    if st.button(
        "↻ Rebuild Dataset",
        use_container_width=True,
    ):
        load_google.clear()
        load_gdelt.clear()
        find_rss.clear()
        load_rss.clear()
        st.rerun()

with toolbar_right:
    estimated_request_note = (
        f"{len(selected_entities)} organization(s) • "
        f"{len(content_languages)} language selection(s) • "
        f"{window_label} • {depth_label} depth"
    )

    st.caption(
        estimated_request_note
    )


selected_registry = registry_df[
    registry_df[
        "Entity_Name"
    ].isin(
        selected_entities
    )
]

all_frames = []
connection_notes = []
retrieval_times = []

with st.spinner(
    "Building research corpus from multiple public sources..."
):
    for _, entity in selected_registry.iterrows():
        entity_name = str(
            entity[
                "Entity_Name"
            ]
        )

        short_name = str(
            entity[
                "Short_Name"
            ]
        )

        query = str(
            entity.get(
                "News_Query",
                "",
            )
        ).strip()

        if (
            not query
            or query.lower() == "nan"
        ):
            query = short_name

        website = str(
            entity.get(
                "Website",
                "",
            )
        ).strip()

        entity_frames = []

        if "Google News" in selected_sources:
            try:
                google_df, retrieved = (
                    load_google(
                        query,
                        tuple(
                            content_languages
                        ),
                        settings[
                            "google_limit"
                        ],
                    )
                )

                if not google_df.empty:
                    google_df = google_df.copy()
                    google_df[
                        "Collection Query"
                    ] = query
                    entity_frames.append(
                        google_df
                    )

                retrieval_times.append(
                    retrieved
                )
            except Exception as error:
                connection_notes.append(
                    f"{short_name} / Google News: {error}"
                )

        if "GDELT" in selected_sources:
            gdelt_queries = [
                query
            ]

            if include_expanded_queries:
                for lens in settings[
                    "lenses"
                ]:
                    gdelt_queries.append(
                        f'("{query}") {lens}'
                    )

            gdelt_frames = []

            for current_query in dict.fromkeys(
                gdelt_queries
            ):
                gdelt_df, gdelt_error, retrieved = (
                    load_gdelt(
                        current_query,
                        window_to_gdelt[
                            window_label
                        ],
                        settings[
                            "gdelt_limit"
                        ],
                    )
                )

                if not gdelt_df.empty:
                    current = gdelt_df.copy()
                    current[
                        "Collection Query"
                    ] = current_query
                    gdelt_frames.append(
                        current
                    )

                if gdelt_error:
                    connection_notes.append(
                        f"{short_name} / GDELT / {current_query}: {gdelt_error}"
                    )

                retrieval_times.append(
                    retrieved
                )

            if gdelt_frames:
                entity_frames.append(
                    pd.concat(
                        gdelt_frames,
                        ignore_index=True,
                    )
                )

        if (
            "Official / Public RSS"
            in selected_sources
            and website
        ):
            feeds, discovery_error = (
                find_rss(
                    website
                )
            )

            if discovery_error:
                connection_notes.append(
                    f"{short_name} / RSS discovery: {discovery_error}"
                )

            if feeds:
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

                rss_df, rss_notes, retrieved = (
                    load_rss(
                        tuple(
                            feeds
                        ),
                        query,
                        official_domain,
                        settings[
                            "rss_limit"
                        ],
                    )
                )

                if not rss_df.empty:
                    rss_df = rss_df.copy()
                    rss_df[
                        "Collection Query"
                    ] = query
                    entity_frames.append(
                        rss_df
                    )

                connection_notes.extend(
                    [
                        f"{short_name} / RSS: {note}"
                        for note in rss_notes
                    ]
                )

                retrieval_times.append(
                    retrieved
                )

        if not entity_frames:
            continue

        entity_df = pd.concat(
            entity_frames,
            ignore_index=True,
        )

        entity_df[
            "Entity"
        ] = short_name

        entity_df[
            "Entity Name"
        ] = entity_name

        entity_df[
            "Home Country"
        ] = entity.get(
            "Country",
            "",
        )

        entity_df[
            "Sector"
        ] = entity.get(
            "Sector",
            "",
        )

        entity_df[
            "Industry"
        ] = entity.get(
            "Industry",
            "",
        )

        all_frames.append(
            entity_df
        )


if not all_frames:
    st.error(
        "No evidence records were returned from the selected sources."
    )

    if connection_notes:
        with st.expander(
            "Connection notes",
            expanded=True,
        ):
            for note in connection_notes:
                st.write(
                    note
                )

    st.stop()


raw_df = pd.concat(
    all_frames,
    ignore_index=True,
)

raw_count = int(
    len(
        raw_df
    )
)

unique_frames = []
cluster_frames = []

for entity_name in raw_df[
    "Entity"
].dropna().unique():
    entity_df = raw_df[
        raw_df[
            "Entity"
        ].eq(
            entity_name
        )
    ].copy()

    entity_df = deduplicate_records(
        entity_df
    )

    entity_df[
        "Published Parsed"
    ] = pd.to_datetime(
        entity_df[
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

    has_date = entity_df[
        "Published Parsed"
    ].notna()

    entity_df = entity_df[
        (
            ~has_date
        )
        | entity_df[
            "Published Parsed"
        ].ge(
            cutoff
        )
    ].copy()

    if entity_df.empty:
        continue

    entity_df, entity_clusters = (
        cluster_narratives(
            entity_df,
            similarity_threshold=cluster_threshold,
        )
    )

    entity_clusters[
        "Entity"
    ] = entity_name

    unique_frames.append(
        entity_df
    )

    cluster_frames.append(
        entity_clusters
    )


if not unique_frames:
    st.warning(
        "No evidence remained after deduplication and evidence-window filtering."
    )
    st.stop()


evidence_df = pd.concat(
    unique_frames,
    ignore_index=True,
)

clusters_df = (
    pd.concat(
        cluster_frames,
        ignore_index=True,
    )
    if cluster_frames
    else pd.DataFrame()
)

unique_count = int(
    len(
        evidence_df
    )
)

source_count = int(
    evidence_df[
        "Source Type"
    ].nunique()
)

language_count = int(
    evidence_df[
        "Language"
    ].nunique()
)

entity_count = int(
    evidence_df[
        "Entity"
    ].nunique()
)


st.markdown(
    '<div class="ti-section-label">Dataset size</div>',
    unsafe_allow_html=True,
)

k1, k2, k3, k4, k5 = st.columns(
    5
)

k1.metric(
    "Raw Records",
    raw_count,
)

k2.metric(
    "Unique Evidence",
    unique_count,
)

k3.metric(
    "Organizations",
    entity_count,
)

k4.metric(
    "Source Types",
    source_count,
)

k5.metric(
    "Languages",
    language_count,
)


dedup_rate = (
    (
        1
        - unique_count
        / max(
            raw_count,
            1,
        )
    )
    * 100
)

st.caption(
    f"Deduplication removed {dedup_rate:.1f}% of raw records. "
    "The Excel export below contains the complete retained corpus, not only the visible preview."
)


entity_summary = (
    evidence_df.groupby(
        "Entity"
    )
    .agg(
        Evidence_Records=(
            "Headline",
            "count",
        ),
        Source_Types=(
            "Source Type",
            "nunique",
        ),
        Languages=(
            "Language",
            "nunique",
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
    )
    .reset_index()
)

entity_summary[
    "Average Sentiment"
] = entity_summary[
    "Average_Sentiment"
].round(
    3
)

entity_summary[
    "Negative Share %"
] = entity_summary[
    "Negative_Share"
].round(
    1
)

entity_summary = entity_summary.drop(
    columns=[
        "Average_Sentiment",
        "Negative_Share",
    ]
)


entity_summary = entity_summary.rename(
    columns={
        "Evidence_Records": "Evidence Records",
        "Source_Types": "Source Types",
    }
)


source_summary = (
    evidence_df.groupby(
        "Source Type"
    )
    .agg(
        Evidence_Records=(
            "Headline",
            "count",
        ),
        Publishers=(
            "Source Name",
            "nunique",
        ),
        Languages=(
            "Language",
            "nunique",
        ),
    )
    .reset_index()
)


source_summary = source_summary.rename(
    columns={
        "Evidence_Records": "Evidence Records",
    }
)


language_summary = (
    evidence_df.groupby(
        "Language"
    )
    .agg(
        Evidence_Records=(
            "Headline",
            "count",
        ),
        Source_Types=(
            "Source Type",
            "nunique",
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
    )
    .reset_index()
)

language_summary[
    "Average Sentiment"
] = language_summary[
    "Average_Sentiment"
].round(
    3
)

language_summary[
    "Negative Share %"
] = language_summary[
    "Negative_Share"
].round(
    1
)

language_summary = language_summary.drop(
    columns=[
        "Average_Sentiment",
        "Negative_Share",
    ]
)


language_summary = language_summary.rename(
    columns={
        "Evidence_Records": "Evidence Records",
        "Source_Types": "Source Types",
    }
)


st.markdown(
    '<div class="ti-section-label">Dataset coverage</div>',
    unsafe_allow_html=True,
)
st.subheader(
    "How much evidence was collected for each organization?"
)

coverage_fig = go.Figure(
    go.Bar(
        x=entity_summary[
            "Evidence Records"
        ],
        y=entity_summary[
            "Entity"
        ],
        orientation="h",
        marker=dict(
            color=categorical_colors(
                len(
                    entity_summary
                )
            ),
            line=dict(
                color="white",
                width=1,
            ),
        ),
        text=entity_summary[
            "Evidence Records"
        ],
        textposition="outside",
        customdata=entity_summary[
            [
                "Source Types",
                "Languages",
                "Negative Share %",
            ]
        ],
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Evidence records: %{x}<br>"
            "Source types: %{customdata[0]}<br>"
            "Languages: %{customdata[1]}<br>"
            "Negative share: %{customdata[2]:.1f}%"
            "<extra></extra>"
        ),
    )
)

coverage_fig.update_layout(
    height=max(
        350,
        65
        * len(
            entity_summary
        ),
    ),
    margin=dict(
        l=10,
        r=55,
        t=10,
        b=30,
    ),
    xaxis=dict(
        title="Unique Evidence Records",
        showgrid=True,
        zeroline=False,
    ),
    yaxis=dict(
        title="",
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    showlegend=False,
    transition=dict(
        duration=450,
        easing="cubic-in-out",
    ),
)

st.plotly_chart(
    coverage_fig,
    use_container_width=True,
    config={
        "displayModeBar": True, "displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 2},
    },
)

render_section_export(
    base_name="TrustIntel_Dataset_Coverage",
    data=entity_summary,
    figure=coverage_fig,
    sheet_name="Dataset Coverage",
)


st.markdown(
    '<div class="ti-section-label">Dataset explorer</div>',
    unsafe_allow_html=True,
)

filter_left, filter_mid, filter_right = st.columns(
    3
)

with filter_left:
    entity_filter = st.multiselect(
        "Filter organizations",
        sorted(
            evidence_df[
                "Entity"
            ]
            .dropna()
            .unique()
            .tolist()
        ),
    )

with filter_mid:
    source_filter = st.multiselect(
        "Filter sources",
        sorted(
            evidence_df[
                "Source Type"
            ]
            .dropna()
            .unique()
            .tolist()
        ),
    )

with filter_right:
    language_filter = st.multiselect(
        "Filter languages",
        sorted(
            evidence_df[
                "Language"
            ]
            .dropna()
            .unique()
            .tolist()
        ),
    )


filtered_df = evidence_df.copy()

if entity_filter:
    filtered_df = filtered_df[
        filtered_df[
            "Entity"
        ].isin(
            entity_filter
        )
    ]

if source_filter:
    filtered_df = filtered_df[
        filtered_df[
            "Source Type"
        ].isin(
            source_filter
        )
    ]

if language_filter:
    filtered_df = filtered_df[
        filtered_df[
            "Language"
        ].isin(
            language_filter
        )
    ]


st.dataframe(
    filtered_df[
        [
            column
            for column in [
                "Entity",
                "Headline",
                "Source Type",
                "Source Class",
                "Source Name",
                "Language",
                "Edition Country",
                "Source Country",
                "Sentiment",
                "Sentiment Label",
                "Published",
                "Collection Query",
                "Link",
            ]
            if column
            in filtered_df.columns
        ]
    ].head(
        250
    ),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Link":
            st.column_config.LinkColumn(
                "Evidence Link",
                display_text="Open",
            )
    },
)

st.caption(
    f"Showing up to 250 rows on screen. The export contains all {len(filtered_df):,} filtered rows."
)

render_section_export(
    base_name="TrustIntel_Dataset_Explorer",
    data=filtered_df.drop(
        columns=[
            "Published Parsed",
        ],
        errors="ignore",
    ),
    sheet_name="Filtered Evidence",
)


st.markdown(
    '<div class="ti-section-label">Full research export</div>',
    unsafe_allow_html=True,
)
st.subheader(
    "Download all evidence and analytical summaries"
)


source_language_summary = (
    evidence_df.groupby(
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

entity_language_summary = (
    evidence_df.groupby(
        [
            "Entity",
            "Language",
        ]
    )
    .size()
    .reset_index(
        name="Evidence Records"
    )
)

metadata = {
    "Dataset Built At": (
        datetime.now(
            timezone.utc
        ).isoformat()
    ),
    "Organizations": ", ".join(
        selected_registry[
            "Short_Name"
        ].astype(str).tolist()
    ),
    "Evidence Window": window_label,
    "Dataset Depth": depth_label,
    "Selected Sources": ", ".join(
        selected_sources
    ),
    "Selected Data Languages": len(
        content_languages
    ),
    "Raw Records": raw_count,
    "Unique Evidence": unique_count,
    "Narrative Clusters": len(
        clusters_df
    ),
    "Cluster Similarity": cluster_threshold,
    "Method Note": (
        "Narrative clustering and risk indicators are prototype analytical outputs. "
        "The evidence sheets retain source links for audit."
    ),
}

excel_bytes = dataframes_to_excel_bytes(
    [
        (
            "Evidence",
            evidence_df.drop(
                columns=[
                    "Canonical Title",
                    "Canonical URL",
                    "Published Parsed",
                ],
                errors="ignore",
            ),
        ),
        (
            "Filtered Evidence",
            filtered_df.drop(
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
            "Entity Summary",
            entity_summary,
        ),
        (
            "Source Summary",
            source_summary,
        ),
        (
            "Language Summary",
            language_summary,
        ),
        (
            "Source x Language",
            source_language_summary,
        ),
        (
            "Entity x Language",
            entity_language_summary,
        ),
    ],
    metadata=metadata,
)

download_left, download_right = st.columns(
    2
)

with download_left:
    st.download_button(
        "⬇ Download Research Dataset (.xlsx)",
        data=excel_bytes,
        file_name=(
            "TrustIntel_Research_Dataset.xlsx"
        ),
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        use_container_width=True,
    )

with download_right:
    csv_bytes = (
        filtered_df.drop(
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
        "⬇ Download Filtered Evidence (.csv)",
        data=csv_bytes,
        file_name=(
            "TrustIntel_Filtered_Evidence.csv"
        ),
        mime="text/csv",
        use_container_width=True,
    )


with st.expander(
    "Connection notes and research limitations"
):
    if connection_notes:
        st.write(
            "**Source connection notes**"
        )

        for note in connection_notes:
            st.write(
                note
            )

    st.write(
        "The visible Streamlit table is intentionally capped for usability, "
        "but the Excel workbook includes the full retained corpus."
    )

    st.write(
        "The maximum data volume depends on what each public source actually returns. "
        "TrustIntel cannot create evidence that does not exist and should not fill gaps "
        "with synthetic narratives."
    )

    st.write(
        "For production-scale longitudinal research, the next infrastructure step is "
        "persistent database storage. That would let TrustIntel accumulate observations "
        "over days and months instead of rebuilding a bounded snapshot on each session."
    )
