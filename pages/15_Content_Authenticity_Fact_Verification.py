import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.chart_theme import PALETTE, POSITIVE_SCALE, categorical_colors
from utils.live_ops import render_live_status
from utils.section_export import render_section_export
from utils.multilingual_content import (
    NEWS_PROFILES,
    get_selected_content_languages,
)
from utils.verification_utils import (
    fetch_url_evidence,
    inspect_image_provenance,
    search_google_news,
    synthetic_text_signals,
    verification_assessment,
)


st.set_page_config(
    page_title="Trust & Verification Console",
    page_icon="✅",
    layout="wide",
)

st.title("Trust & Verification Console")

render_live_status(
    [
        ("Evidence search", "ON-DEMAND"),
        ("Source retrieval", "ON-DEMAND"),
        ("Provenance", "ON-DEMAND"),
        ("Verification scores", "PROTOTYPE"),
    ],
    note=(
        "Evidence is retrieved when a claim is submitted. Verification scores are "
        "prototype decision-support measures and do not claim absolute truth."
    ),
)

st.caption(
    "Assess a claim against source credibility, corroborating public evidence, "
    "language coverage and available synthetic-content provenance signals."
)

st.warning(
    "TrustIntel AI does not claim absolute truth and does not infer AI generation "
    "from writing style alone. Unknown or insufficient evidence remains explicitly uncertain."
)

selected_languages = get_selected_content_languages()

language_labels = [
    NEWS_PROFILES.get(
        code,
        {},
    ).get(
        "label",
        code,
    )
    for code in selected_languages
]

st.markdown(
    '<div class="ti-section-label">Verification workflow</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="ti-workflow">
        <div class="ti-step">
            <div class="ti-step-num">01</div>
            <div class="ti-step-title">Claim Intake</div>
            <div class="ti-step-copy">Capture the statement, source and optional media.</div>
        </div>
        <div class="ti-step">
            <div class="ti-step-num">02</div>
            <div class="ti-step-title">Source Check</div>
            <div class="ti-step-copy">Assess identifiable source and institutional credibility signals.</div>
        </div>
        <div class="ti-step">
            <div class="ti-step-num">03</div>
            <div class="ti-step-title">Evidence Search</div>
            <div class="ti-step-copy">Search corroborating evidence across selected language editions.</div>
        </div>
        <div class="ti-step">
            <div class="ti-step-num">04</div>
            <div class="ti-step-title">Reliability Scoring</div>
            <div class="ti-step-copy">Combine factual reliability, source credibility and evidence coverage.</div>
        </div>
        <div class="ti-step">
            <div class="ti-step-num">05</div>
            <div class="ti-step-title">Provenance Review</div>
            <div class="ti-step-copy">Inspect declared synthetic or edit metadata without overclaiming.</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="ti-section-label">Claim intake</div>',
    unsafe_allow_html=True,
)

claim = st.text_area(
    "Claim or content to verify",
    height=130,
    placeholder=(
        "Paste the statement, post, headline, or narrative you want to assess."
    ),
    key="trustintel_verification_claim",
)

source_col, publisher_col = st.columns(2)

with source_col:
    source_url = st.text_input(
        "Source URL (optional)",
        key="trustintel_verification_url",
    )

with publisher_col:
    source_name = st.text_input(
        "Source or publisher name (optional)",
        key="trustintel_verification_source",
    )

uploaded_image = st.file_uploader(
    "Upload an image for provenance metadata inspection (optional)",
    type=[
        "png",
        "jpg",
        "jpeg",
        "webp",
        "tif",
        "tiff",
    ],
    key="trustintel_verification_image",
)

st.caption(
    "Evidence languages: "
    + ", ".join(language_labels)
)

if not claim.strip():
    st.info(
        "Enter a claim to begin verification. "
        "The results console will appear below once evidence collection starts."
    )
    st.stop()


# ---------------------------
# Evidence collection
# ---------------------------
evidence_frames = []

with st.spinner(
    "Collecting multilingual corroborating evidence..."
):
    for code in selected_languages:
        try:
            frame = search_google_news(
                claim,
                limit=12,
                language_code=code,
            )

            if not frame.empty:
                evidence_frames.append(
                    frame
                )
        except Exception:
            continue

if evidence_frames:
    evidence_df = pd.concat(
        evidence_frames,
        ignore_index=True,
    )

    evidence_df = (
        evidence_df.drop_duplicates(
            subset=[
                "Headline",
                "Source",
            ],
            keep="first",
        )
        .sort_values(
            "Similarity",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )
else:
    evidence_df = pd.DataFrame()

fetched = (
    fetch_url_evidence(
        source_url
    )
    if source_url
    else {}
)

assessment = verification_assessment(
    claim=claim,
    source_url=source_url,
    source_name=source_name,
    evidence_df=evidence_df,
    fetched=fetched,
)

source_text = (
    fetched.get(
        "text",
        "",
    )
    if fetched.get(
        "ok"
    )
    else claim
)

synthetic_text = synthetic_text_signals(
    source_text,
    metadata=fetched.get(
        "metadata",
        {},
    ),
)

image_result = (
    inspect_image_provenance(
        uploaded_image.getvalue()
    )
    if uploaded_image is not None
    else None
)


# ---------------------------
# Verdict
# ---------------------------
status = assessment["Status"]
frs = float(assessment["FRS"])
scs = float(assessment["SCS"])
ecs = float(assessment["ECS"])
confidence = assessment[
    "Verification Confidence"
]
strong_count = int(
    assessment[
        "Strong Corroborations"
    ]
)
moderate_count = int(
    assessment[
        "Moderate Corroborations"
    ]
)

if status == "Supported":
    decision_copy = (
        "The current evidence set provides comparatively strong support for the claim. "
        "Review the corroborating sources and provenance notes before relying on it operationally."
    )
elif status == "Partially supported":
    decision_copy = (
        "The claim has meaningful support, but the evidence is not yet strong enough "
        "for an unqualified conclusion."
    )
elif status == "Unverified":
    decision_copy = (
        "The available evidence is insufficient to verify the claim. "
        "Absence of corroboration is not proof that the claim is false."
    )
else:
    decision_copy = (
        "The current evidence set provides weak support or conflicting signals. "
        "The claim should not be treated as established without stronger evidence."
    )

st.markdown(
    '<div class="ti-section-label">Verification decision</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="ti-verdict">
        <div class="ti-verdict-label">Current Evidence-Based Verdict</div>
        <div class="ti-verdict-status">{status}</div>
        <div class="ti-verdict-copy">
            {decision_copy}
            <br><br>
            <strong>Verification confidence:</strong> {confidence}
            &nbsp;•&nbsp;
            <strong>Source assessment:</strong> {assessment["Source Note"]}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric(
    "Factual Reliability",
    f"{frs:.1f}",
    help="FRS: Factual Reliability Score",
)

k2.metric(
    "Source Credibility",
    f"{scs:.1f}",
    help="SCS: Source Credibility Score",
)

k3.metric(
    "Evidence Coverage",
    f"{ecs:.1f}",
    help="ECS: Evidence Coverage Score",
)

k4.metric(
    "Strong Corroborations",
    strong_count,
)

k5.metric(
    "Confidence",
    confidence,
)


# ---------------------------
# Score visual + evidence strength
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Evidence strength</div>',
    unsafe_allow_html=True,
)
st.subheader("How strong is the current verification basis?")

score_left, score_right = st.columns([1, 1.25])

with score_left:
    gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=frs,
            title={
                "text": "Factual Reliability Score"
            },
            gauge={
                "axis": {
                    "range": [0, 100]
                },
                "bar": {
                    "color": (
                        PALETTE["green"]
                        if frs >= 75
                        else PALETTE["teal"]
                        if frs >= 55
                        else PALETTE["orange"]
                        if frs >= 35
                        else PALETTE["red"]
                    ),
                    "thickness": 0.32,
                },
                "steps": [
                    {
                        "range": [0, 35],
                        "color": "rgba(239,68,68,.13)",
                    },
                    {
                        "range": [35, 55],
                        "color": "rgba(245,158,11,.14)",
                    },
                    {
                        "range": [55, 75],
                        "color": "rgba(14,143,176,.14)",
                    },
                    {
                        "range": [75, 100],
                        "color": "rgba(16,185,129,.16)",
                    },
                ],
                "threshold": {
                    "line": {
                        "color": PALETTE["navy"],
                        "width": 3,
                    },
                    "thickness": 0.75,
                    "value": frs,
                },
            },
        )
    )

    gauge.update_layout(
        height=360,
        margin=dict(
            l=25,
            r=25,
            t=55,
            b=20,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        transition=dict(duration=500, easing="cubic-in-out"),
    )

    st.plotly_chart(
        gauge,
        use_container_width=True,
        config={
            "displayModeBar": True, "displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 2},
        },
    )

    verification_scores = pd.DataFrame(
        {
            "Metric": [
                "Factual Reliability",
                "Source Credibility",
                "Evidence Coverage",
            ],
            "Score": [
                frs,
                scs,
                ecs,
            ],
        }
    )

    render_section_export(
        base_name="TrustIntel_Verification_Reliability_Gauge",
        data=verification_scores,
        figure=gauge,
        sheet_name="Verification Scores",
    )

with score_right:
    score_fig = go.Figure(
        go.Bar(
            x=[
                frs,
                scs,
                ecs,
            ],
            y=[
                "Factual Reliability",
                "Source Credibility",
                "Evidence Coverage",
            ],
            orientation="h",
            text=[
                f"{frs:.1f}",
                f"{scs:.1f}",
                f"{ecs:.1f}",
            ],
            textposition="outside",
            marker=dict(
                color=[
                    PALETTE["teal"],
                    PALETTE["blue"],
                    PALETTE["violet"],
                ],
                line=dict(color="white", width=1),
            ),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Score: %{x:.1f}/100"
                "<extra></extra>"
            ),
        )
    )

    score_fig.update_layout(
        height=360,
        margin=dict(
            l=10,
            r=55,
            t=25,
            b=25,
        ),
        xaxis=dict(
            title="Score",
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
        score_fig,
        use_container_width=True,
        config={
            "displayModeBar": True, "displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 2},
        },
    )

    render_section_export(
        base_name="TrustIntel_Verification_Score_Comparison",
        data=verification_scores,
        figure=score_fig,
        sheet_name="Score Comparison",
    )


# ---------------------------
# Corroboration distribution
# ---------------------------
if not evidence_df.empty:
    similarities = evidence_df[
        "Similarity"
    ].fillna(0)

    evidence_df = evidence_df.copy()

    evidence_df[
        "Evidence Strength"
    ] = similarities.apply(
        lambda value:
        "Strong"
        if value >= 0.18
        else (
            "Moderate"
            if value >= 0.10
            else "Weak / contextual"
        )
    )

    strength_counts = (
        evidence_df[
            "Evidence Strength"
        ]
        .value_counts()
        .reindex(
            [
                "Strong",
                "Moderate",
                "Weak / contextual",
            ],
            fill_value=0,
        )
        .reset_index()
    )

    strength_counts.columns = [
        "Evidence Strength",
        "Records",
    ]

    strength_fig = go.Figure(
        go.Bar(
            x=strength_counts[
                "Evidence Strength"
            ],
            y=strength_counts[
                "Records"
            ],
            text=strength_counts[
                "Records"
            ],
            textposition="outside",
            marker=dict(
                color=[
                    PALETTE["green"],
                    PALETTE["orange"],
                    PALETTE["slate"],
                ],
                line=dict(color="white", width=1),
            ),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Evidence records: %{y}"
                "<extra></extra>"
            ),
        )
    )

    strength_fig.update_layout(
        height=330,
        margin=dict(
            l=15,
            r=15,
            t=20,
            b=25,
        ),
        xaxis=dict(
            title="",
        ),
        yaxis=dict(
            title="Evidence records",
            showgrid=True,
            zeroline=False,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        transition=dict(duration=450, easing="cubic-in-out"),
    )

    st.plotly_chart(
        strength_fig,
        use_container_width=True,
        config={
            "displayModeBar": True, "displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 2},
        },
    )

    render_section_export(
        base_name="TrustIntel_Verification_Corroboration_Strength",
        data=strength_counts,
        figure=strength_fig,
        sheet_name="Evidence Strength",
    )


# ---------------------------
# Multilingual corroboration
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Multilingual corroboration</div>',
    unsafe_allow_html=True,
)
st.subheader("Where does corroborating evidence appear?")

if evidence_df.empty:
    st.info(
        "No matching multilingual news evidence was returned."
    )
else:
    if (
        "Evidence Language"
        in evidence_df.columns
    ):
        language_summary = (
            evidence_df.groupby(
                "Evidence Language"
            )
            .agg(
                Evidence_Records=(
                    "Headline",
                    "count",
                ),
                Average_Similarity=(
                    "Similarity",
                    "mean",
                ),
            )
            .reset_index()
        )

        language_summary[
            "Average Similarity"
        ] = (
            language_summary[
                "Average_Similarity"
            ]
            .mul(100)
            .round(1)
        )

        lang_fig = go.Figure(
            go.Bar(
                x=language_summary[
                    "Evidence_Records"
                ],
                y=language_summary[
                    "Evidence Language"
                ],
                orientation="h",
                text=language_summary[
                    "Evidence_Records"
                ],
                textposition="outside",
                marker=dict(
                    color=categorical_colors(
                        len(language_summary)
                    ),
                    line=dict(
                        color="white",
                        width=1,
                    ),
                ),
                customdata=language_summary[
                    [
                        "Average Similarity",
                    ]
                ],
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Evidence records: %{x}<br>"
                    "Average text overlap index: %{customdata[0]:.1f}"
                    "<extra></extra>"
                ),
            )
        )

        lang_fig.update_layout(
            height=max(
                340,
                52 * len(
                    language_summary
                ),
            ),
            margin=dict(
                l=10,
                r=50,
                t=10,
                b=25,
            ),
            xaxis=dict(
                title="Corroborating evidence records",
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
            lang_fig,
            use_container_width=True,
            config={
                "displayModeBar": True, "displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 2},
            },
        )

        render_section_export(
            base_name="TrustIntel_Verification_Language_Coverage",
            data=language_summary,
            figure=lang_fig,
            sheet_name="Language Coverage",
        )


# ---------------------------
# Source + provenance
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Source and provenance</div>',
    unsafe_allow_html=True,
)
st.subheader("What can we establish about the source and synthetic origin?")

source_panel, synthetic_panel = st.columns(2)

with source_panel:
    if source_url:
        if fetched.get("ok"):
            st.success(
                "Source URL successfully retrieved."
            )

            s1, s2 = st.columns(2)

            s1.metric(
                "Source Credibility",
                f"{scs:.1f}",
            )

            s2.metric(
                "Retrieval Status",
                "Available",
            )

            st.write(
                "**Domain:**",
                fetched.get(
                    "domain",
                    "",
                ),
            )

            st.write(
                "**Page title:**",
                fetched.get(
                    "title",
                    "",
                ),
            )

            st.caption(
                assessment[
                    "Source Note"
                ]
            )
        else:
            st.warning(
                "The source URL could not be retrieved."
            )

            st.write(
                "**Domain:**",
                fetched.get(
                    "domain",
                    "",
                ),
            )

            st.caption(
                fetched.get(
                    "error",
                    "",
                )
            )
    else:
        st.info(
            "No source URL supplied. Source credibility is therefore limited by the available publisher information."
        )

with synthetic_panel:
    p1, p2, p3 = st.columns(3)

    p1.metric(
        "Provenance Signal",
        synthetic_text[
            "label"
        ],
    )

    p2.metric(
        "Synthetic Risk",
        synthetic_text[
            "score"
        ],
    )

    p3.metric(
        "Confidence",
        synthetic_text[
            "confidence"
        ],
    )

    st.write(
        synthetic_text[
            "evidence"
        ]
    )

    st.caption(
        "A low or unknown provenance signal does not prove that content is authentic. "
        "The system only reports evidence it can support."
    )


# ---------------------------
# Evidence table
# ---------------------------
st.markdown(
    '<div class="ti-section-label">Corroborating evidence</div>',
    unsafe_allow_html=True,
)
st.subheader("Evidence behind the verdict")

if evidence_df.empty:
    st.info(
        "No corroborating evidence records are available."
    )
else:
    display_cols = [
        "Evidence Strength",
        "Headline",
        "Source",
        "Evidence Language",
        "Similarity",
        "Link",
    ]

    st.dataframe(
        evidence_df[
            [
                column
                for column
                in display_cols
                if column
                in evidence_df.columns
            ]
        ].head(25),
        use_container_width=True,
        hide_index=True,
    )

    render_section_export(
        base_name="TrustIntel_Verification_Corroborating_Evidence",
        data=evidence_df,
        sheet_name="Corroborating Evidence",
    )

    with st.expander(
        "Full multilingual evidence audit"
    ):
        st.dataframe(
            evidence_df,
            use_container_width=True,
            hide_index=True,
        )


# ---------------------------
# Optional image provenance
# ---------------------------
if image_result:
    st.markdown(
        '<div class="ti-section-label">Image provenance</div>',
        unsafe_allow_html=True,
    )
    st.subheader(
        "Uploaded image metadata assessment"
    )

    i1, i2, i3 = st.columns(3)

    i1.metric(
        "Image Signal",
        image_result[
            "label"
        ],
    )

    i2.metric(
        "Synthetic / Edit Risk",
        image_result[
            "score"
        ],
    )

    i3.metric(
        "Confidence",
        image_result[
            "confidence"
        ],
    )

    st.write(
        image_result[
            "evidence"
        ]
    )

    if image_result.get(
        "metadata"
    ):
        with st.expander(
            "Image metadata"
        ):
            st.json(
                image_result[
                    "metadata"
                ]
            )


# ---------------------------
# Methodology
# ---------------------------
with st.expander(
    "Verification methodology and limitations"
):
    st.write(
        "FRS is a prototype Factual Reliability Score combining source credibility, "
        "evidence coverage and available source-text similarity. SCS is a source-credibility "
        "indicator based on identifiable domain/source characteristics. ECS measures the "
        "coverage of corroborating evidence using similarity thresholds."
    )

    st.write(
        "Strong corroborations use a prototype similarity threshold of 0.18 or above; "
        "moderate corroborations use 0.10 or above. These thresholds are comparative "
        "research heuristics and should be calibrated on validated multilingual datasets "
        "before production use."
    )

    st.write(
        "Synthetic-origin assessment looks for declared provenance or metadata signals. "
        "It does not classify text as AI-generated based only on writing style, and "
        "absence of provenance metadata is not evidence of authenticity."
    )
