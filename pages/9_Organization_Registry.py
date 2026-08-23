import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.chart_theme import (
    categorical_colors,
)
from utils.glossary import (
    render_glossary,
)
from utils.live_ops import (
    render_live_status,
)
from utils.registry_utils import (
    load_portfolio_memberships,
    load_registry,
    portfolio_catalog,
    portfolio_entity_ids,
    portfolio_names,
)
from utils.section_export import (
    render_section_export,
)


st.set_page_config(
    page_title="Strategic Organization Registry",
    page_icon="🏢",
    layout="wide",
)

st.title(
    "🏢 Strategic Organization Registry"
)

st.caption(
    "Navigate TrustIntel AI by market, portfolio, country and sector instead of a single long organization list."
)

render_live_status(
    [
        (
            "Core Registry",
            "LIVE",
        ),
        (
            "Strategic Expansion",
            "LIVE",
        ),
        (
            "Portfolio Layer",
            "LIVE",
        ),
    ],
    note=(
        "The registry combines the existing organization base with a strategic "
        "GCC and global AI expansion layer. Portfolio membership is curated for "
        "client comparison and can be changed without altering the core registry."
    ),
)

render_glossary(
    [
        "CIK",
    ]
)

try:
    df = load_registry()
except FileNotFoundError:
    st.error(
        "Registry file not found: config/entity_registry.csv"
    )
    st.stop()

memberships = (
    load_portfolio_memberships()
)

catalog = (
    portfolio_catalog()
)


# ---------------------------
# Portfolio membership column
# ---------------------------
if not memberships.empty:
    membership_text = (
        memberships.groupby(
            "Entity_ID"
        )[
            "Portfolio"
        ]
        .apply(
            lambda values:
            ", ".join(
                sorted(
                    set(
                        values
                    )
                )
            )
        )
        .to_dict()
    )
else:
    membership_text = {}

df[
    "Portfolios"
] = (
    df[
        "Entity_ID"
    ]
    .astype(str)
    .map(
        membership_text
    )
    .fillna(
        ""
    )
)


# ---------------------------
# Registry KPIs
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Registry coverage</div>',
    unsafe_allow_html=True,
)

k1, k2, k3, k4, k5 = st.columns(
    5
)

k1.metric(
    "Organizations",
    len(
        df
    ),
)

k2.metric(
    "Regions",
    df[
        "Region"
    ].nunique(),
)

k3.metric(
    "Countries",
    df[
        "Country"
    ].nunique(),
)

k4.metric(
    "Sectors",
    df[
        "Sector"
    ].nunique(),
)

k5.metric(
    "Portfolios",
    len(
        catalog
    ),
)


# ---------------------------
# Portfolio quick access
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Strategic portfolios</div>',
    unsafe_allow_html=True,
)

st.subheader(
    "Start from a client use case"
)

portfolio_options = [
    "All portfolios",
] + portfolio_names()

selected_portfolio = (
    st.selectbox(
        "Portfolio",
        portfolio_options,
        index=0,
    )
)

if (
    selected_portfolio
    != "All portfolios"
    and not catalog.empty
):
    selected_catalog = (
        catalog[
            catalog[
                "Portfolio"
            ].eq(
                selected_portfolio
            )
        ]
    )

    if not selected_catalog.empty:
        description = (
            selected_catalog.iloc[
                0
            ][
                "Description"
            ]
        )

        st.info(
            description
        )


# ---------------------------
# Client filters
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Organization finder</div>',
    unsafe_allow_html=True,
)

filtered = df.copy()

portfolio_ids = portfolio_entity_ids(
    selected_portfolio
)

if portfolio_ids:
    filtered = filtered[
        filtered[
            "Entity_ID"
        ]
        .astype(str)
        .isin(
            [
                str(value)
                for value
                in portfolio_ids
            ]
        )
    ]


f1, f2, f3, f4 = st.columns(
    4
)

with f1:
    region_filter = st.multiselect(
        "Region",
        sorted(
            filtered[
                "Region"
            ]
            .dropna()
            .unique()
            .tolist()
        ),
    )

if region_filter:
    filtered = filtered[
        filtered[
            "Region"
        ].isin(
            region_filter
        )
    ]

with f2:
    country_filter = st.multiselect(
        "Country",
        sorted(
            filtered[
                "Country"
            ]
            .dropna()
            .unique()
            .tolist()
        ),
        format_func=lambda value:
        str(
            value
        ).replace(
            "_",
            " ",
        ),
    )

if country_filter:
    filtered = filtered[
        filtered[
            "Country"
        ].isin(
            country_filter
        )
    ]

with f3:
    sector_filter = st.multiselect(
        "Sector",
        sorted(
            filtered[
                "Sector"
            ]
            .dropna()
            .unique()
            .tolist()
        ),
        format_func=lambda value:
        str(
            value
        ).replace(
            "_",
            " ",
        ),
    )

if sector_filter:
    filtered = filtered[
        filtered[
            "Sector"
        ].isin(
            sector_filter
        )
    ]

with f4:
    type_filter = st.multiselect(
        "Organization Type",
        sorted(
            filtered[
                "Entity_Type"
            ]
            .dropna()
            .unique()
            .tolist()
        ),
        format_func=lambda value:
        str(
            value
        ).replace(
            "_",
            " ",
        ),
    )

if type_filter:
    filtered = filtered[
        filtered[
            "Entity_Type"
        ].isin(
            type_filter
        )
    ]


search = st.text_input(
    "🔍 Search organizations, industries, countries or query fields"
)

if search:
    search_columns = [
        "Entity_Name",
        "Short_Name",
        "Country",
        "Region",
        "Sector",
        "Industry",
        "News_Query",
        "Google_Trends_Query",
        "Search_Query",
        "YouTube_Query",
        "Portfolios",
    ]

    search_mask = pd.Series(
        False,
        index=filtered.index,
    )

    for column in search_columns:
        search_mask = (
            search_mask
            | filtered[
                column
            ]
            .astype(str)
            .str.contains(
                search,
                case=False,
                na=False,
            )
        )

    filtered = filtered[
        search_mask
    ]


st.caption(
    f"{len(filtered):,} organization(s) match the current registry scope."
)


# ---------------------------
# Coverage visuals
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Coverage balance</div>',
    unsafe_allow_html=True,
)

chart_left, chart_right = st.columns(
    2
)

with chart_left:
    region_summary = (
        filtered[
            "Region"
        ]
        .value_counts()
        .rename_axis(
            "Region"
        )
        .reset_index(
            name="Organizations"
        )
    )

    region_fig = go.Figure(
        go.Bar(
            x=region_summary[
                "Organizations"
            ],
            y=region_summary[
                "Region"
            ],
            orientation="h",
            marker=dict(
                color=categorical_colors(
                    len(
                        region_summary
                    )
                ),
                line=dict(
                    color="white",
                    width=1,
                ),
            ),
            text=region_summary[
                "Organizations"
            ],
            textposition="outside",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Organizations: %{x}"
                "<extra></extra>"
            ),
        )
    )

    region_fig.update_layout(
        height=max(
            360,
            52
            * len(
                region_summary
            ),
        ),
        margin=dict(
            l=10,
            r=45,
            t=10,
            b=30,
        ),
        xaxis=dict(
            title="Organizations",
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
        region_fig,
        use_container_width=True,
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "toImageButtonOptions": {
                "format": "png",
                "scale": 2,
            },
        },
    )

    render_section_export(
        base_name="TrustIntel_Registry_By_Region",
        data=region_summary,
        figure=region_fig,
        sheet_name="Registry by Region",
    )


with chart_right:
    sector_summary = (
        filtered[
            "Sector"
        ]
        .value_counts()
        .head(
            15
        )
        .rename_axis(
            "Sector"
        )
        .reset_index(
            name="Organizations"
        )
    )

    sector_summary[
        "Sector"
    ] = (
        sector_summary[
            "Sector"
        ]
        .astype(str)
        .str.replace(
            "_",
            " ",
            regex=False,
        )
    )

    sector_fig = go.Figure(
        go.Bar(
            x=sector_summary[
                "Organizations"
            ],
            y=sector_summary[
                "Sector"
            ],
            orientation="h",
            marker=dict(
                color=categorical_colors(
                    len(
                        sector_summary
                    )
                ),
                line=dict(
                    color="white",
                    width=1,
                ),
            ),
            text=sector_summary[
                "Organizations"
            ],
            textposition="outside",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Organizations: %{x}"
                "<extra></extra>"
            ),
        )
    )

    sector_fig.update_layout(
        height=max(
            360,
            44
            * len(
                sector_summary
            ),
        ),
        margin=dict(
            l=10,
            r=45,
            t=10,
            b=30,
        ),
        xaxis=dict(
            title="Organizations",
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
            duration=450,
            easing="cubic-in-out",
        ),
    )

    st.plotly_chart(
        sector_fig,
        use_container_width=True,
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "toImageButtonOptions": {
                "format": "png",
                "scale": 2,
            },
        },
    )

    render_section_export(
        base_name="TrustIntel_Registry_By_Sector",
        data=sector_summary,
        figure=sector_fig,
        sheet_name="Registry by Sector",
    )


# ---------------------------
# Registry table
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Registry</div>',
    unsafe_allow_html=True,
)

display_columns = [
    "Entity_ID",
    "Display_Name",
    "Short_Name",
    "Entity_Type",
    "Region",
    "Country",
    "Sector",
    "Industry",
    "Priority",
    "Portfolios",
    "Website",
]

registry_view = (
    filtered[
        display_columns
    ]
    .rename(
        columns={
            "Display_Name":
                "Organization",
        }
    )
    .sort_values(
        [
            "Region",
            "Country",
            "Organization",
        ]
    )
)

st.dataframe(
    registry_view,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Website":
            st.column_config.LinkColumn(
                "Website",
                display_text="Open",
            )
    },
)

render_section_export(
    base_name="TrustIntel_Filtered_Organization_Registry",
    data=registry_view,
    sheet_name="Organization Registry",
)


# ---------------------------
# Organization profile
# ---------------------------
if not filtered.empty:
    option_ids = (
        filtered[
            "Entity_ID"
        ]
        .astype(str)
        .tolist()
    )

    label_map = {
        str(row["Entity_ID"]): (
            f'{row["Short_Name"]}  ·  '
            f'{str(row["Country"]).replace("_", " ")}  ·  '
            f'{str(row["Sector"]).replace("_", " ")}'
        )
        for _, row
        in filtered.iterrows()
    }

    selected_id = st.selectbox(
        "Select organization for profile",
        option_ids,
        format_func=lambda value:
        label_map.get(
            str(value),
            str(value),
        ),
    )

    profile = (
        filtered[
            filtered[
                "Entity_ID"
            ]
            .astype(str)
            .eq(
                str(
                    selected_id
                )
            )
        ]
        .iloc[
            0
        ]
    )

    st.markdown(
        '<div class="ti-section-label">Organization profile</div>',
        unsafe_allow_html=True,
    )

    p1, p2, p3, p4, p5 = st.columns(
        5
    )

    p1.metric(
        "Organization",
        profile[
            "Short_Name"
        ],
    )

    p2.metric(
        "Region",
        profile[
            "Region"
        ],
    )

    p3.metric(
        "Country",
        str(
            profile[
                "Country"
            ]
        ).replace(
            "_",
            " ",
        ),
    )

    p4.metric(
        "Sector",
        str(
            profile[
                "Sector"
            ]
        ).replace(
            "_",
            " ",
        ),
    )

    p5.metric(
        "Priority",
        profile[
            "Priority"
        ],
    )

    if st.button(
        "Use this organization across TrustIntel AI",
        type="primary",
    ):
        st.session_state[
            "trustintel_selected_entity_id"
        ] = str(
            profile[
                "Entity_ID"
            ]
        )

        st.success(
            f'{profile["Short_Name"]} is now the preferred organization '
            "for intelligence modules that use the global organization selector."
        )

    profile_left, profile_right = st.columns(
        2
    )

    with profile_left:
        st.write(
            "**Organization type:**",
            str(
                profile[
                    "Entity_Type"
                ]
            ).replace(
                "_",
                " ",
            ),
        )

        st.write(
            "**Industry:**",
            str(
                profile[
                    "Industry"
                ]
            ).replace(
                "_",
                " ",
            ),
        )

        st.write(
            "**Portfolios:**",
            profile[
                "Portfolios"
            ]
            or "Not assigned",
        )

        st.write(
            "**Data source type:**",
            profile[
                "Data_Source_Type"
            ],
        )

        ticker = str(
            profile[
                "Ticker"
            ]
        ).strip()

        if (
            ticker
            and ticker.lower()
            != "nan"
        ):
            st.write(
                "**Ticker:**",
                ticker,
            )

        cik = str(
            profile[
                "CIK"
            ]
        ).strip()

        if (
            cik
            and cik.lower()
            != "nan"
        ):
            st.write(
                "**CIK:**",
                cik,
            )

    with profile_right:
        st.write(
            "**News query:**",
            profile[
                "News_Query"
            ],
        )

        st.write(
            "**Google Trends query:**",
            profile[
                "Google_Trends_Query"
            ],
        )

        st.write(
            "**Search query:**",
            profile[
                "Search_Query"
            ],
        )

        st.write(
            "**YouTube query:**",
            profile[
                "YouTube_Query"
            ],
        )

        website = str(
            profile[
                "Website"
            ]
        ).strip()

        if (
            website
            and website.lower()
            != "nan"
        ):
            st.link_button(
                "Open Official Website",
                website,
            )


# ---------------------------
# Portfolio catalog
# ---------------------------
with st.expander(
    "Portfolio catalog and membership"
):
    st.dataframe(
        catalog,
        use_container_width=True,
        hide_index=True,
    )

    if not memberships.empty:
        portfolio_members = (
            memberships.merge(
                df[
                    [
                        "Entity_ID",
                        "Short_Name",
                        "Region",
                        "Country",
                        "Sector",
                    ]
                ],
                on="Entity_ID",
                how="left",
            )
        )

        st.dataframe(
            portfolio_members,
            use_container_width=True,
            hide_index=True,
        )


with st.expander(
    "Registry design note"
):
    st.write(
        "TrustIntel now keeps the original organization registry intact and "
        "adds new strategic organizations through a separate expansion file. "
        "This avoids repeatedly rewriting the large core registry and makes "
        "regional expansion easier to maintain."
    )

    st.write(
        "Region is derived from the organization country. Portfolios are curated "
        "comparison groups rather than mutually exclusive classifications, so one "
        "organization can appear in multiple portfolios."
    )
