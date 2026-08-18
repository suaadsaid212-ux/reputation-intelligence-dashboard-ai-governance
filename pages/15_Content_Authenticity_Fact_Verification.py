import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.verification_utils import (
    claim_sentiment,
    fetch_url_evidence,
    inspect_image_provenance,
    search_google_news,
    synthetic_text_signals,
    verification_assessment,
)


st.set_page_config(
    page_title=(
        "Content Authenticity & "
        "Fact Verification"
    ),
    page_icon="✓",
    layout="wide",
)

st.title(
    "Content Authenticity & Fact Verification"
)

st.caption(
    "Evidence-based claim checking, source "
    "credibility assessment, and cautious "
    "synthetic-content provenance signals."
)

st.warning(
    "This prototype does not claim to determine "
    "absolute truth or prove AI generation from "
    "style alone. Synthetic-origin labels are "
    "reported as unknown unless provenance or "
    "metadata provides meaningful evidence."
)

claim = st.text_area(
    "Claim or content to verify",
    height=150,
    placeholder=(
        "Paste the statement, post, headline, "
        "or narrative you want to assess."
    ),
)

source_url = st.text_input(
    "Source URL (optional)"
)

source_name = st.text_input(
    "Source or publisher name (optional)"
)

uploaded_image = st.file_uploader(
    "Upload an image for provenance metadata "
    "inspection (optional)",
    type=[
        "png",
        "jpg",
        "jpeg",
        "webp",
        "tif",
        "tiff",
    ],
)

if not claim.strip():
    st.info(
        "Enter a claim to begin verification."
    )
    st.stop()

with st.spinner(
    "Collecting corroborating evidence..."
):
    evidence_df = search_google_news(
        claim,
        limit=20,
    )

fetched = fetch_url_evidence(
    source_url
) if source_url else {}

assessment = verification_assessment(
    claim=claim,
    source_url=source_url,
    source_name=source_name,
    evidence_df=evidence_df,
    fetched=fetched,
)

source_text = (
    fetched.get("text", "")
    if fetched.get("ok")
    else claim
)

synthetic_text = synthetic_text_signals(
    source_text,
    metadata=fetched.get(
        "metadata",
        {},
    ),
)

image_result = None

if uploaded_image is not None:
    image_result = (
        inspect_image_provenance(
            uploaded_image.getvalue()
        )
    )

st.subheader(
    "Verification Decision"
)

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric(
    "Status",
    assessment["Status"],
)
k2.metric(
    "FRS",
    assessment["FRS"],
    help="Factual Reliability Score",
)
k3.metric(
    "SCS",
    assessment["SCS"],
    help="Source Credibility Score",
)
k4.metric(
    "ECS",
    assessment["ECS"],
    help="Evidence Coverage Score",
)
k5.metric(
    "Confidence",
    assessment[
        "Verification Confidence"
    ],
)

st.caption(
    assessment["Source Note"]
)

score_chart = go.Figure(
    go.Bar(
        x=["FRS", "SCS", "ECS"],
        y=[
            assessment["FRS"],
            assessment["SCS"],
            assessment["ECS"],
        ],
        text=[
            assessment["FRS"],
            assessment["SCS"],
            assessment["ECS"],
        ],
        textposition="auto",
    )
)
score_chart.update_layout(
    height=380,
    yaxis_range=[0, 100],
    yaxis_title="Score",
)
st.plotly_chart(
    score_chart,
    use_container_width=True,
)

st.subheader(
    "Corroborating Evidence"
)

if evidence_df.empty:
    st.info(
        "No matching Google News evidence "
        "was returned for this claim."
    )
else:
    st.dataframe(
        evidence_df,
        use_container_width=True,
        hide_index=True,
    )

    strong = evidence_df[
        evidence_df["Similarity"] >= 0.18
    ]

    moderate = evidence_df[
        evidence_df["Similarity"] >= 0.10
    ]

    st.write(
        f"Strong corroborations: "
        f"{len(strong)}"
    )
    st.write(
        f"Moderate corroborations: "
        f"{len(moderate)}"
    )

st.subheader(
    "Source Evidence"
)

if source_url:
    if fetched.get("ok"):
        st.success(
            "Source URL was successfully read."
        )
        st.write(
            "**Domain:**",
            fetched.get("domain", ""),
        )
        st.write(
            "**Page title:**",
            fetched.get("title", ""),
        )
    else:
        st.warning(
            "The source URL could not be "
            "retrieved."
        )
        st.write(
            fetched.get("error", "")
        )
else:
    st.info(
        "No source URL supplied."
    )

st.subheader(
    "Synthetic-Origin Assessment"
)

s1, s2, s3 = st.columns(3)

s1.metric(
    "Text / Page Signal",
    synthetic_text["label"],
)
s2.metric(
    "Synthetic Risk",
    synthetic_text["score"],
)
s3.metric(
    "Confidence",
    synthetic_text[
        "confidence"
    ],
)

st.write(
    synthetic_text["evidence"]
)

if image_result:
    st.write(
        "### Uploaded Image Provenance"
    )

    i1, i2, i3 = st.columns(3)

    i1.metric(
        "Image Signal",
        image_result["label"],
    )
    i2.metric(
        "Synthetic / Edit Risk",
        image_result["score"],
    )
    i3.metric(
        "Confidence",
        image_result[
            "confidence"
        ],
    )

    st.write(
        image_result["evidence"]
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

st.subheader(
    "Claim Context"
)

st.write(
    "**Claim sentiment:**",
    claim_sentiment(claim),
)

st.write(
    "**Interpretation:** "
    "The verification score reflects source "
    "quality and corroboration available to "
    "this prototype. It should support human "
    "review, not replace it."
)
