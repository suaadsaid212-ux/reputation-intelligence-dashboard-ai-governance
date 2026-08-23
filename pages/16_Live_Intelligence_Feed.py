from datetime import datetime, timedelta, timezone

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.chart_theme import (
    PALETTE,
    RISK_SCALE,
    categorical_colors,
)
from utils.section_export import render_section_export
from utils.live_ops import (
    render_live_status,
    source_health_frame,
)
from utils.multilingual_content import (
    fetch_multilingual_news,
    get_selected_content_languages,
)


st.set_page_config(
    page_title="Live Intelligence Feed",
    page_icon="⚡",
    layout="wide",
)

st.title("Live Intelligence Feed")

st.caption(
    "Current multilingual public intelligence with explicit source freshness, "
    "refresh state and change detection."
)

render_live_status(
    [
        ("News source", "LIVE"),
        ("Feed cache", "CACHED"),
        ("Risk priority", "PROTOTYPE"),
    ],
    note=(
        "Google News RSS is queried as a live public source. "
        "Results are cached for up to 10 minutes for performance. "
        "Signal Priority is a prototype decision-support indicator."
    ),
)

try:
    registry_df = pd.read_csv(
        "config/entity_registry.csv",
        encoding="utf-8-sig",
    )
except FileNotFoundError:
    st.error(
        "Registry file not found: config/entity_registry.csv"
    )
    st.stop()


content_languages = get_selected_content_languages()

entity_options = (
    registry_df[
        "Entity_Name"
    ]
    .dropna()
    .astype(str)
    .tolist()
)

default_entities = (
    entity_options[:3]
)

selected_entities = st.sidebar.multiselect(
    "Organizations",
    entity_options,
    default=default_entities,
)

window_label = st.sidebar.selectbox(
    "Evidence window",
    [
        "24 Hours",
        "7 Days",
        "30 Days",
        "All returned",
    ],
    index=1,
)

limit_per_language = st.sidebar.slider(
    "Rows per language / entity",
    min_value=3,
    max_value=10,
    value=5,
    step=1,
)

if not selected_entities:
    st.warning(
        "Select at least one organization."
    )
    st.stop()


@st.cache_data(
    ttl=600,
    show_spinner=False,
)
def load_live_entity_news(
    query,
    languages,
    limit_per_language,
):
    frame = fetch_multilingual_news(
        query=query,
        languages=list(languages),
        limit_per_language=int(
            limit_per_language
        ),
    )

    retrieved_at = (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )

    return frame, retrieved_at


frames = []
retrieval_times = []

selected_registry = registry_df[
    registry_df[
        "Entity_Name"
    ].isin(
        selected_entities
    )
]

with st.spinner(
    "Retrieving current multilingual signals..."
):
    for _, entity in selected_registry.iterrows():
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
            query = str(
                entity[
                    "Entity_Name"
                ]
            )

        frame, retrieved_at = (
            load_live_entity_news(
                query,
                tuple(
                    content_languages
                ),
                limit_per_language,
            )
        )

        retrieval_times.append(
            retrieved_at
        )

        if frame.empty:
            continue

        current = frame.copy()

        current[
            "Entity"
        ] = entity[
            "Short_Name"
        ]

        current[
            "Entity Name"
        ] = entity[
            "Entity_Name"
        ]

        current[
            "Sector"
        ] = entity.get(
            "Sector",
            "",
        )

        current[
            "Home Country"
        ] = entity.get(
            "Country",
            "",
        )

        frames.append(
            current
        )


if frames:
    feed = pd.concat(
        frames,
        ignore_index=True,
    )
else:
    feed = pd.DataFrame()


if feed.empty:
    st.warning(
        "No current public intelligence rows were returned "
        "for the selected organizations and languages."
    )
    st.stop()


feed = (
    feed.drop_duplicates(
        subset=[
            "Entity",
            "Headline",
            "Source",
        ],
        keep="first",
    )
    .reset_index(
        drop=True
    )
)

feed[
    "Published Parsed"
] = pd.to_datetime(
    feed.get(
        "Published",
        pd.Series(
            index=feed.index,
            dtype="object",
        ),
    ),
    errors="coerce",
    utc=True,
)


now_utc = datetime.now(
    timezone.utc
)

window_map = {
    "24 Hours": timedelta(
        hours=24
    ),
    "7 Days": timedelta(
        days=7
    ),
    "30 Days": timedelta(
        days=30
    ),
}

if window_label in window_map:
    cutoff = (
        now_utc
        - window_map[
            window_label
        ]
    )

    windowed = feed[
        feed[
            "Published Parsed"
        ].ge(
            cutoff
        )
    ].copy()
else:
    windowed = feed.copy()


if windowed.empty:
    st.warning(
        f"No signals with a parseable publication date were found "
        f"inside the selected {window_label.lower()} window. "
        "Choose a wider evidence window to inspect older returned records."
    )
    st.stop()


windowed[
    "Hours Old"
] = (
    (
        pd.Timestamp(
            now_utc
        )
        - windowed[
            "Published Parsed"
        ]
    )
    .dt.total_seconds()
    .div(
        3600
    )
    .clip(
        lower=0
    )
)


sentiment_pressure = (
    (
        1
        - windowed[
            "Sentiment"
        ].fillna(
            0
        )
    )
    * 50
).clip(
    0,
    100,
)

recency_score = (
    100
    - windowed[
        "Hours Old"
    ]
    .div(
        24 * 7
    )
    .mul(
        100
    )
).clip(
    0,
    100,
)


windowed[
    "Signal Priority"
] = (
    sentiment_pressure
    * .70
    + recency_score
    * .30
).clip(
    0,
    100,
).round(
    1
)


windowed[
    "Signal Key"
] = (
    windowed[
        "Entity"
    ].astype(str)
    + "|"
    + windowed[
        "Headline"
    ].astype(str)
    + "|"
    + windowed[
        "Source"
    ].astype(str)
)


windowed = windowed.sort_values(
    [
        "Published Parsed",
        "Signal Priority",
    ],
    ascending=[
        False,
        False,
    ],
).reset_index(
    drop=True
)


signal_keys = set(
    windowed[
        "Signal Key"
    ].tolist()
)

latest_age_hours = float(
    windowed[
        "Hours Old"
    ].min()
)

current_summary = {
    "latest_age_hours": latest_age_hours,
    "signals": int(
        len(windowed)
    ),
    "negative_share": float(
        windowed[
            "Sentiment"
        ]
        .lt(
            -0.05
        )
        .mean()
        * 100
    ),
    "languages": int(
        windowed[
            "Language"
        ].nunique()
    ),
    "entities": int(
        windowed[
            "Entity"
        ].nunique()
    ),
}

previous_keys = st.session_state.get(
    "ti_live_previous_keys"
)

previous_summary = st.session_state.get(
    "ti_live_previous_summary"
)

if previous_keys is None:
    new_signals = None
else:
    new_signals = len(
        signal_keys
        - set(
            previous_keys
        )
    )


latest_retrieval = (
    max(
        retrieval_times
    )
    if retrieval_times
    else ""
)

try:
    retrieval_dt = datetime.fromisoformat(
        latest_retrieval
    )
    retrieval_label = retrieval_dt.strftime(
        "%d %b %Y • %H:%M:%S UTC"
    )
except Exception:
    retrieval_label = "Unavailable"


toolbar_left, toolbar_right = st.columns(
    [
        4,
        1,
    ]
)

with toolbar_left:
    st.caption(
        f"Evidence retrieved: {retrieval_label} • "
        f"Window: {window_label} • "
        f"Languages requested: {len(content_languages)}"
    )

with toolbar_right:
    if st.button(
        "↻ Refresh Live Feed",
        use_container_width=True,
    ):
        st.session_state[
            "ti_live_previous_keys"
        ] = list(
            signal_keys
        )

        st.session_state[
            "ti_live_previous_summary"
        ] = current_summary

        load_live_entity_news.clear()

        st.rerun()


negative_delta = None
language_delta = None
signal_delta = None

if previous_summary:
    negative_delta = round(
        current_summary[
            "negative_share"
        ]
        - previous_summary.get(
            "negative_share",
            0,
        ),
        1,
    )

    language_delta = (
        current_summary[
            "languages"
        ]
        - previous_summary.get(
            "languages",
            0,
        )
    )

    signal_delta = (
        current_summary[
            "signals"
        ]
        - previous_summary.get(
            "signals",
            0,
        )
    )


st.markdown(
    '<div class="ti-section-label">Live operations snapshot</div>',
    unsafe_allow_html=True,
)

k1, k2, k3, k4, k5, k6 = st.columns(
    6
)

k1.metric(
    "Current Signals",
    current_summary[
        "signals"
    ],
    delta=signal_delta,
)

k2.metric(
    "New Since Refresh",
    (
        new_signals
        if new_signals
        is not None
        else "—"
    ),
)

k3.metric(
    "Negative Share",
    f"{current_summary['negative_share']:.1f}%",
    delta=(
        f"{negative_delta:+.1f} pp"
        if negative_delta
        is not None
        else None
    ),
    delta_color="inverse",
)

k4.metric(
    "Languages Observed",
    current_summary[
        "languages"
    ],
    delta=language_delta,
)

k5.metric(
    "Entities Active",
    current_summary[
        "entities"
    ],
)

latest_age = current_summary[
    "latest_age_hours"
]

if latest_age < 1:
    latest_age_label = "< 1 hour"
elif latest_age < 24:
    latest_age_label = f"{latest_age:.0f} hours"
else:
    latest_age_label = f"{latest_age / 24:.1f} days"

k6.metric(
    "Latest Signal Age",
    latest_age_label,
)


if previous_summary:
    change_message = (
        f"<strong>{new_signals}</strong> new signal(s) appeared since the "
        f"previous manual refresh. Negative share changed by "
        f"<strong>{negative_delta:+.1f} percentage points</strong>, and "
        f"language coverage changed by <strong>{language_delta:+d}</strong>."
    )
else:
    change_message = (
        "This is the current baseline. Press "
        "<strong>Refresh Live Feed</strong> after a few minutes to compare "
        "the next live evidence set and surface genuinely new signals."
    )


st.markdown(
    f"""
    <div class="ti-feed-alert">
        <div class="ti-feed-kicker">Since Last Refresh</div>
        <div class="ti-feed-copy">
            {change_message}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    '<div class="ti-section-label">Current signal landscape</div>',
    unsafe_allow_html=True,
)
st.subheader(
    "Where is current attention concentrated?"
)

chart_left, chart_right = st.columns(
    [
        1.05,
        .95,
    ]
)

entity_summary = (
    windowed.groupby(
        "Entity"
    )
    .agg(
        Signals=(
            "Headline",
            "count",
        ),
        Average_Priority=(
            "Signal Priority",
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
    "Average Priority"
] = entity_summary[
    "Average_Priority"
].round(
    1
)

entity_summary[
    "Negative Share %"
] = entity_summary[
    "Negative_Share"
].round(
    1
)


with chart_left:
    entity_plot = entity_summary.sort_values(
        "Average Priority",
        ascending=True,
    )

    entity_fig = go.Figure(
        go.Bar(
            x=entity_plot[
                "Average Priority"
            ],
            y=entity_plot[
                "Entity"
            ],
            orientation="h",
            text=entity_plot[
                "Average Priority"
            ],
            textposition="outside",
            marker=dict(
                color=entity_plot[
                    "Average Priority"
                ],
                colorscale=RISK_SCALE,
                cmin=0,
                cmax=100,
                line=dict(
                    color="white",
                    width=1,
                ),
            ),
            customdata=entity_plot[
                [
                    "Signals",
                    "Negative Share %",
                ]
            ],
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Average Signal Priority: %{x:.1f}<br>"
                "Current Signals: %{customdata[0]}<br>"
                "Negative Share: %{customdata[1]:.1f}%"
                "<extra></extra>"
            ),
        )
    )

    entity_fig.update_layout(
        height=max(
            340,
            64
            * len(
                entity_plot
            ),
        ),
        margin=dict(
            l=10,
            r=55,
            t=10,
            b=30,
        ),
        xaxis=dict(
            title="Signal Priority",
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
        transition=dict(
            duration=450,
            easing="cubic-in-out",
        ),
    )

    st.plotly_chart(
        entity_fig,
        use_container_width=True,
        config={
            "displayModeBar": True, "displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 2},
        },
    )

    render_section_export(
        base_name="TrustIntel_Live_Entity_Signals",
        data=entity_summary,
        figure=entity_fig,
        sheet_name="Entity Signals",
    )


with chart_right:
    language_summary = (
        windowed[
            "Language"
        ]
        .value_counts()
        .rename_axis(
            "Language"
        )
        .reset_index(
            name="Signals"
        )
    )

    lang_colors = categorical_colors(
        len(
            language_summary
        )
    )

    lang_fig = go.Figure(
        go.Bar(
            x=language_summary[
                "Signals"
            ],
            y=language_summary[
                "Language"
            ],
            orientation="h",
            marker=dict(
                color=lang_colors,
                line=dict(
                    color="white",
                    width=1,
                ),
            ),
            text=language_summary[
                "Signals"
            ],
            textposition="outside",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Current signals: %{x}"
                "<extra></extra>"
            ),
        )
    )

    lang_fig.update_layout(
        height=max(
            340,
            48
            * len(
                language_summary
            ),
        ),
        margin=dict(
            l=10,
            r=45,
            t=10,
            b=30,
        ),
        xaxis=dict(
            title="Signals",
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
        lang_fig,
        use_container_width=True,
        config={
            "displayModeBar": True, "displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 2},
        },
    )

    render_section_export(
        base_name="TrustIntel_Live_Language_Distribution",
        data=language_summary,
        figure=lang_fig,
        sheet_name="Language Distribution",
    )


st.markdown(
    '<div class="ti-section-label">Live evidence stream</div>',
    unsafe_allow_html=True,
)
st.subheader(
    "Most recent multilingual signals"
)

display_columns = [
    "Published",
    "Entity",
    "Headline",
    "Language",
    "Edition Country",
    "Source",
    "Sentiment",
    "Sentiment Label",
    "Signal Priority",
    "Link",
]

display = windowed[
    [
        column
        for column in display_columns
        if column
        in windowed.columns
    ]
].head(
    100
)


column_config = {}

if (
    "Signal Priority"
    in display.columns
):
    column_config[
        "Signal Priority"
    ] = st.column_config.ProgressColumn(
        "Signal Priority",
        help=(
            "Prototype prioritization combining sentiment pressure "
            "and recency. Not an automated judgment of harm."
        ),
        min_value=0,
        max_value=100,
        format="%.1f",
    )

if "Link" in display.columns:
    column_config[
        "Link"
    ] = st.column_config.LinkColumn(
        "Evidence Link",
        display_text="Open",
    )


st.dataframe(
    display,
    use_container_width=True,
    hide_index=True,
    column_config=column_config,
)

render_section_export(
    base_name="TrustIntel_Live_Evidence_Stream",
    data=windowed.drop(
        columns=[
            "Published Parsed",
        ],
        errors="ignore",
    ),
    sheet_name="Live Evidence",
)


st.markdown(
    '<div class="ti-section-label">Operational source map</div>',
    unsafe_allow_html=True,
)
st.subheader(
    "Which TrustIntel AI signals are truly live?"
)

health = source_health_frame(
    [
        [
            "Multilingual News",
            "LIVE + 10 min cache",
            "On refresh / TTL expiry",
            "Selected data languages",
            "Used by Live Feed, Executive, Crisis and governance-related monitoring.",
        ],
        [
            "Public Social Sources",
            "ON-DEMAND / mixed",
            "Page refresh / source API",
            "Depends on connected platform",
            "YouTube, Reddit, Hacker News, Mastodon and Bluesky availability varies by connector.",
        ],
        [
            "Google Trends",
            "ON-DEMAND",
            "When Trends module runs",
            "Selected aliases / markets",
            "Current search-interest connector; exact freshness depends on Google Trends.",
        ],
        [
            "Verification Evidence",
            "ON-DEMAND",
            "When a claim is submitted",
            "Selected language editions",
            "Live corroborating news search and optional source URL retrieval.",
        ],
        [
            "Crisis Composite",
            "PROTOTYPE",
            "Recomputed on page load",
            "News + proxy components",
            "Live multilingual news is combined with current prototype proxy inputs.",
        ],
        [
            "AI / Reputation Scores",
            "PROTOTYPE",
            "Recomputed from current evidence",
            "Module-specific",
            "Comparative decision-support indicators, not automated legal or compliance judgments.",
        ],
    ]
)

st.dataframe(
    health,
    use_container_width=True,
    hide_index=True,
)


with st.expander(
    "How live change detection works"
):
    st.write(
        "The Live Intelligence Feed stores the current signal identifiers "
        "in the Streamlit session when you press Refresh. It then retrieves "
        "the next evidence set and compares the entity, headline and source "
        "combinations against that prior snapshot."
    )

    st.write(
        "This is session-level operational change detection. It is not yet "
        "a persistent enterprise event store. A production version would "
        "persist observations in a database, maintain time-series histories "
        "and trigger alerts when configurable thresholds are crossed."
    )
