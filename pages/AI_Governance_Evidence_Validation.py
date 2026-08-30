from __future__ import annotations

import hashlib
import io
import math
from datetime import datetime, timezone
from itertools import combinations

import numpy as np
import pandas as pd
import streamlit as st

try:
    import krippendorff
except ImportError:
    krippendorff = None


st.set_page_config(
    page_title="AI Governance Evidence Validation",
    page_icon="📋",
    layout="wide",
)


GOVERNANCE_DOMAINS = [
    "Leadership accountability",
    "AI risk assessment",
    "Human oversight",
    "Data governance",
    "Transparency and documentation",
    "Monitoring and auditing",
    "Incident response and correction",
    "Stakeholder complaint, redress and learning",
]

EVIDENCE_LEVELS = {
    0: "No public evidence located",
    1: "Aspirational",
    2: "Procedural",
    3: "Implemented",
    4: "Verified",
}

RATING_COLUMNS = [
    "Relevance",
    "Clarity",
    "Observability",
    "Distinctiveness",
    "Practical_Usefulness",
    "Cross_Country_Suitability",
]

CORPUS_COLUMNS = [
    "Unit_ID",
    "Document_ID",
    "Organization",
    "Country",
    "Sector",
    "Document_Type",
    "Publication_Date",
    "Source_URL",
    "Document_Language",
    "Passage",
    "Proposed_Governance_Domain",
    "Notes",
]

CODING_COLUMNS = CORPUS_COLUMNS + [
    "Governance_Domain",
    "Evidence_Level",
    "Evidence_Label",
    "Decision_Rationale",
    "Confidence",
    "Ambiguous",
    "Manual_Version",
    "Coder_ID",
    "Coded_At_UTC",
]

CHANGE_LOG_COLUMNS = [
    "Change_ID",
    "Date_UTC",
    "Manual_Version_From",
    "Manual_Version_To",
    "Indicator_ID",
    "Original_Wording",
    "Problem_Identified",
    "Evidence_Source",
    "Revised_Wording",
    "Reason",
    "Decision",
    "Approved_By",
]


def default_manual() -> pd.DataFrame:
    rows = [
        {
            "Indicator_ID": "AIG_01",
            "Governance_Domain": "Leadership accountability",
            "Indicator_Name": "Assigned AI accountability",
            "Definition": "Public identification of a role, committee or governing body accountable for AI oversight.",
            "Inclusion_Rule": "Code when the document assigns responsibility for AI governance, approval, escalation or oversight.",
            "Exclusion_Rule": "Exclude general leadership support without an assigned governance responsibility.",
            "Positive_Example": "The board risk committee reviews material AI risks quarterly.",
            "Ambiguous_Example": "Senior leaders support responsible innovation.",
            "Evidence_Required": "Named role or body, stated responsibility and governance activity.",
            "Source_Frameworks": "ISO/IEC 42001; NIST AI RMF Govern; OECD accountability",
            "Manual_Version": "1.0",
            "Status": "Draft",
        },
        {
            "Indicator_ID": "AIG_02",
            "Governance_Domain": "AI risk assessment",
            "Indicator_Name": "AI risk and impact assessment",
            "Definition": "A documented process for identifying, evaluating and prioritising AI related risks and impacts.",
            "Inclusion_Rule": "Code explicit assessments, risk classification, impact assessment or documented approval gates.",
            "Exclusion_Rule": "Exclude unstructured claims that the organisation considers risk.",
            "Positive_Example": "Every high impact AI use case completes an impact assessment before deployment.",
            "Ambiguous_Example": "We carefully consider the risks of AI.",
            "Evidence_Required": "Assessment scope, timing, responsible role or reported application.",
            "Source_Frameworks": "NIST AI RMF Map and Measure; ISO/IEC 42001; EU AI Act",
            "Manual_Version": "1.0",
            "Status": "Draft",
        },
        {
            "Indicator_ID": "AIG_03",
            "Governance_Domain": "Human oversight",
            "Indicator_Name": "Meaningful human review",
            "Definition": "Human authority to review, challenge, intervene in or reverse material AI outputs or decisions.",
            "Inclusion_Rule": "Code when review authority, intervention points or decision responsibility are specified.",
            "Exclusion_Rule": "Exclude generic human centred language without a review or intervention mechanism.",
            "Positive_Example": "A trained employee approves every externally published generative AI communication.",
            "Ambiguous_Example": "Our AI remains human centred.",
            "Evidence_Required": "Defined reviewer, review stage and authority to intervene.",
            "Source_Frameworks": "EU AI Act human oversight; OECD human centred values; NIST AI RMF",
            "Manual_Version": "1.0",
            "Status": "Draft",
        },
        {
            "Indicator_ID": "AIG_04",
            "Governance_Domain": "Data governance",
            "Indicator_Name": "Governed AI data lifecycle",
            "Definition": "Controls over the quality, provenance, permission, privacy and retention of data used by AI systems.",
            "Inclusion_Rule": "Code specific AI data controls, provenance requirements, privacy reviews or retention procedures.",
            "Exclusion_Rule": "Exclude a generic privacy policy that makes no connection to AI use or governance.",
            "Positive_Example": "Training data are documented for provenance, permitted use, quality and retention.",
            "Ambiguous_Example": "We respect customer privacy.",
            "Evidence_Required": "Identifiable control applied to AI related data.",
            "Source_Frameworks": "ISO/IEC 42001; NIST AI RMF; OECD privacy and data governance",
            "Manual_Version": "1.0",
            "Status": "Draft",
        },
        {
            "Indicator_ID": "AIG_05",
            "Governance_Domain": "Transparency and documentation",
            "Indicator_Name": "Traceable AI use and decisions",
            "Definition": "Documentation that makes AI use, purpose, limitations, decisions and accountability traceable.",
            "Inclusion_Rule": "Code disclosure, system documentation, model records, decision logs or traceability requirements.",
            "Exclusion_Rule": "Exclude promotional descriptions of AI capabilities without governance documentation.",
            "Positive_Example": "The organisation keeps a register of material AI systems, owners, purposes and limitations.",
            "Ambiguous_Example": "We are transparent about technology.",
            "Evidence_Required": "Specified documentation or disclosure mechanism.",
            "Source_Frameworks": "NIST AI RMF; ISO/IEC 42001; OECD transparency; EU AI Act",
            "Manual_Version": "1.0",
            "Status": "Draft",
        },
        {
            "Indicator_ID": "AIG_06",
            "Governance_Domain": "Monitoring and auditing",
            "Indicator_Name": "Ongoing AI monitoring and assurance",
            "Definition": "Post deployment monitoring, testing, internal audit or independent assurance of AI systems and controls.",
            "Inclusion_Rule": "Code defined monitoring, testing frequency, audit activity, reported findings or independent assurance.",
            "Exclusion_Rule": "Exclude initial testing claims with no ongoing monitoring or assurance process.",
            "Positive_Example": "High risk systems undergo quarterly performance monitoring and annual independent assurance.",
            "Ambiguous_Example": "Our AI systems are regularly checked.",
            "Evidence_Required": "Monitoring or audit method, frequency, responsibility, result or assurance source.",
            "Source_Frameworks": "NIST AI RMF Measure and Manage; ISO/IEC 42001",
            "Manual_Version": "1.0",
            "Status": "Draft",
        },
        {
            "Indicator_ID": "AIG_07",
            "Governance_Domain": "Incident response and correction",
            "Indicator_Name": "AI incident response and correction",
            "Definition": "Procedures to identify, escalate, investigate, correct and communicate material AI failures or harms.",
            "Inclusion_Rule": "Code explicit AI incident channels, escalation steps, correction procedures or published corrective action.",
            "Exclusion_Rule": "Exclude generic crisis management language with no connection to AI related incidents.",
            "Positive_Example": "AI incidents are logged, escalated to the risk committee and followed by documented corrective action.",
            "Ambiguous_Example": "We respond quickly when problems occur.",
            "Evidence_Required": "AI related trigger, escalation, investigation or correction mechanism.",
            "Source_Frameworks": "NIST AI RMF Manage; ISO/IEC 42001; EU AI Act",
            "Manual_Version": "1.0",
            "Status": "Draft",
        },
        {
            "Indicator_ID": "AIG_08",
            "Governance_Domain": "Stakeholder complaint, redress and learning",
            "Indicator_Name": "Stakeholder challenge and organisational learning",
            "Definition": "Accessible mechanisms for stakeholders to question AI outcomes, seek correction or redress and inform governance improvement.",
            "Inclusion_Rule": "Code complaint, appeal, contestability, remediation, feedback or documented learning mechanisms connected to AI.",
            "Exclusion_Rule": "Exclude a general customer service channel unless it explicitly covers AI affected outcomes.",
            "Positive_Example": "Customers may challenge an AI assisted outcome and request human reconsideration and correction.",
            "Ambiguous_Example": "Customers can contact us with questions.",
            "Evidence_Required": "AI specific challenge, redress, feedback or learning mechanism.",
            "Source_Frameworks": "OECD accountability; NIST AI RMF; ISO/IEC 42001",
            "Manual_Version": "1.0",
            "Status": "Draft",
        },
    ]
    return pd.DataFrame(rows)


def empty_corpus() -> pd.DataFrame:
    return pd.DataFrame(columns=CORPUS_COLUMNS)


def empty_change_log() -> pd.DataFrame:
    return pd.DataFrame(columns=CHANGE_LOG_COLUMNS)


def initialise_state() -> None:
    defaults = {
        "aig_manual": default_manual(),
        "aig_corpus": empty_corpus(),
        "aig_pilot": empty_corpus(),
        "aig_change_log": empty_change_log(),
        "aig_adjudicated": pd.DataFrame(),
        "aig_manual_frozen": False,
        "aig_manual_version": "1.0",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


def dataframes_to_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for name, df in sheets.items():
            safe_name = name[:31]
            df.to_excel(writer, sheet_name=safe_name, index=False)
    return buffer.getvalue()


def read_uploaded_table(uploaded_file) -> pd.DataFrame:
    suffix = uploaded_file.name.lower().rsplit(".", 1)[-1]
    if suffix in {"xlsx", "xlsm", "xls"}:
        return pd.read_excel(uploaded_file)
    if suffix in {"csv", "txt"}:
        return pd.read_csv(uploaded_file)
    raise ValueError("Upload a CSV or Excel file.")


def normalise_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def add_unit_ids(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    if "Unit_ID" not in result.columns:
        result["Unit_ID"] = ""
    for index, row in result.iterrows():
        if normalise_text(row.get("Unit_ID")):
            continue
        source = "|".join(
            [
                normalise_text(row.get("Document_ID")),
                normalise_text(row.get("Organization")),
                normalise_text(row.get("Source_URL")),
                normalise_text(row.get("Passage")),
                str(index),
            ]
        )
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]
        result.at[index, "Unit_ID"] = f"UNIT_{digest.upper()}"
    return result


def align_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    result = df.copy()
    for column in columns:
        if column not in result.columns:
            result[column] = pd.NA
    return result[columns]


def missing_required_columns(df: pd.DataFrame, required: list[str]) -> list[str]:
    return [column for column in required if column not in df.columns]


def stratified_pilot_sample(
    corpus: pd.DataFrame,
    fraction: float,
    minimum_units: int,
    strata_columns: list[str],
    seed: int,
) -> pd.DataFrame:
    if corpus.empty:
        return corpus.copy()

    corpus = corpus.reset_index(drop=True).copy()
    target = min(
        len(corpus),
        max(int(math.ceil(len(corpus) * fraction)), minimum_units),
    )
    rng = np.random.default_rng(seed)

    valid_strata = [column for column in strata_columns if column in corpus.columns]
    if not valid_strata:
        chosen = rng.choice(corpus.index.to_numpy(), size=target, replace=False)
        return corpus.loc[chosen].sort_values("Unit_ID").reset_index(drop=True)

    strata_frame = corpus[valid_strata].fillna("Not stated").astype(str)
    stratum_key = strata_frame.agg(" | ".join, axis=1)
    groups = [index.to_numpy() for _, index in corpus.groupby(stratum_key).groups.items()]

    selected: list[int] = []
    if len(groups) <= target:
        for group_indices in groups:
            selected.append(int(rng.choice(group_indices)))

    remaining_pool = np.array(
        [index for index in corpus.index if index not in set(selected)],
        dtype=int,
    )
    remaining_needed = target - len(selected)
    if remaining_needed > 0:
        additional = rng.choice(
            remaining_pool,
            size=remaining_needed,
            replace=False,
        )
        selected.extend(int(index) for index in additional)

    return corpus.loc[selected].sort_values("Unit_ID").reset_index(drop=True)


def unweighted_cohen_kappa(values_a: pd.Series, values_b: pd.Series) -> float:
    paired = pd.DataFrame({"a": values_a, "b": values_b}).dropna()
    if paired.empty:
        return float("nan")
    categories = sorted(set(paired["a"]).union(set(paired["b"])), key=str)
    observed = float((paired["a"] == paired["b"]).mean())
    expected = 0.0
    for category in categories:
        expected += float((paired["a"] == category).mean()) * float(
            (paired["b"] == category).mean()
        )
    if np.isclose(1.0 - expected, 0.0):
        return 1.0 if np.isclose(observed, 1.0) else float("nan")
    return (observed - expected) / (1.0 - expected)


def quadratic_weighted_kappa(values_a: pd.Series, values_b: pd.Series) -> float:
    paired = pd.DataFrame(
        {
            "a": pd.to_numeric(values_a, errors="coerce"),
            "b": pd.to_numeric(values_b, errors="coerce"),
        }
    ).dropna()
    if paired.empty:
        return float("nan")

    categories = sorted(set(paired["a"]).union(set(paired["b"])))
    category_index = {category: index for index, category in enumerate(categories)}
    size = len(categories)
    if size == 1:
        return 1.0

    observed = np.zeros((size, size), dtype=float)
    for first, second in paired.itertuples(index=False):
        observed[category_index[first], category_index[second]] += 1
    observed /= observed.sum()

    first_marginal = observed.sum(axis=1)
    second_marginal = observed.sum(axis=0)
    expected = np.outer(first_marginal, second_marginal)

    weights = np.zeros((size, size), dtype=float)
    denominator = float((size - 1) ** 2)
    for first_index in range(size):
        for second_index in range(size):
            weights[first_index, second_index] = (
                (first_index - second_index) ** 2 / denominator
            )

    observed_disagreement = float((weights * observed).sum())
    expected_disagreement = float((weights * expected).sum())
    if np.isclose(expected_disagreement, 0.0):
        return 1.0 if np.isclose(observed_disagreement, 0.0) else float("nan")
    return 1.0 - observed_disagreement / expected_disagreement


def pairwise_reliability(codings: pd.DataFrame) -> pd.DataFrame:
    rows = []
    coder_ids = sorted(codings["Coder_ID"].dropna().astype(str).unique())
    for coder_a, coder_b in combinations(coder_ids, 2):
        first = codings[codings["Coder_ID"].astype(str) == coder_a].copy()
        second = codings[codings["Coder_ID"].astype(str) == coder_b].copy()
        paired = first.merge(second, on="Unit_ID", suffixes=("_A", "_B"))
        if paired.empty:
            continue
        rows.append(
            {
                "Coder_A": coder_a,
                "Coder_B": coder_b,
                "Shared_Units": len(paired),
                "Exact_Domain_Agreement": round(
                    float(
                        (
                            paired["Governance_Domain_A"]
                            == paired["Governance_Domain_B"]
                        ).mean()
                    ),
                    3,
                ),
                "Domain_Cohen_Kappa": round(
                    unweighted_cohen_kappa(
                        paired["Governance_Domain_A"],
                        paired["Governance_Domain_B"],
                    ),
                    3,
                ),
                "Exact_Evidence_Agreement": round(
                    float(
                        (
                            pd.to_numeric(paired["Evidence_Level_A"], errors="coerce")
                            == pd.to_numeric(
                                paired["Evidence_Level_B"], errors="coerce"
                            )
                        ).mean()
                    ),
                    3,
                ),
                "Quadratic_Weighted_Kappa": round(
                    quadratic_weighted_kappa(
                        paired["Evidence_Level_A"],
                        paired["Evidence_Level_B"],
                    ),
                    3,
                ),
            }
        )
    return pd.DataFrame(rows)


def krippendorff_results(codings: pd.DataFrame) -> tuple[float, float]:
    if krippendorff is None:
        return float("nan"), float("nan")

    evidence_pivot = codings.pivot_table(
        index="Coder_ID",
        columns="Unit_ID",
        values="Evidence_Level",
        aggfunc="first",
    ).apply(pd.to_numeric, errors="coerce")

    evidence_alpha = float("nan")
    if evidence_pivot.shape[0] >= 2 and evidence_pivot.shape[1] >= 2:
        evidence_alpha = float(
            krippendorff.alpha(
                reliability_data=evidence_pivot.to_numpy(dtype=float),
                level_of_measurement="ordinal",
            )
        )

    domain_source = codings[["Coder_ID", "Unit_ID", "Governance_Domain"]].copy()
    domain_values = sorted(domain_source["Governance_Domain"].dropna().unique())
    domain_map = {value: index for index, value in enumerate(domain_values)}
    domain_source["Domain_Code"] = domain_source["Governance_Domain"].map(domain_map)
    domain_pivot = domain_source.pivot_table(
        index="Coder_ID",
        columns="Unit_ID",
        values="Domain_Code",
        aggfunc="first",
    )

    domain_alpha = float("nan")
    if domain_pivot.shape[0] >= 2 and domain_pivot.shape[1] >= 2:
        domain_alpha = float(
            krippendorff.alpha(
                reliability_data=domain_pivot.to_numpy(dtype=float),
                level_of_measurement="nominal",
            )
        )

    return evidence_alpha, domain_alpha


def disagreement_table(codings: pd.DataFrame) -> pd.DataFrame:
    domain = codings.pivot_table(
        index="Unit_ID",
        columns="Coder_ID",
        values="Governance_Domain",
        aggfunc="first",
    )
    evidence = codings.pivot_table(
        index="Unit_ID",
        columns="Coder_ID",
        values="Evidence_Level",
        aggfunc="first",
    )
    domain.columns = [f"Domain_{column}" for column in domain.columns]
    evidence.columns = [f"Evidence_{column}" for column in evidence.columns]
    comparison = domain.join(evidence, how="outer")

    domain_columns = [column for column in comparison if column.startswith("Domain_")]
    evidence_columns = [
        column for column in comparison if column.startswith("Evidence_")
    ]

    def row_disagrees(row: pd.Series, columns: list[str]) -> bool:
        values = [normalise_text(row[column]) for column in columns]
        values = [value for value in values if value]
        return len(set(values)) > 1

    comparison["Domain_Disagreement"] = comparison.apply(
        lambda row: row_disagrees(row, domain_columns), axis=1
    )
    comparison["Evidence_Disagreement"] = comparison.apply(
        lambda row: row_disagrees(row, evidence_columns), axis=1
    )
    comparison = comparison[
        comparison["Domain_Disagreement"] | comparison["Evidence_Disagreement"]
    ].reset_index()

    metadata_columns = [
        "Unit_ID",
        "Document_ID",
        "Organization",
        "Country",
        "Sector",
        "Document_Type",
        "Source_URL",
        "Passage",
    ]
    metadata = codings[
        [column for column in metadata_columns if column in codings.columns]
    ].drop_duplicates("Unit_ID")
    return metadata.merge(comparison, on="Unit_ID", how="right")


def adjudication_template(codings: pd.DataFrame) -> pd.DataFrame:
    metadata_columns = [
        "Unit_ID",
        "Document_ID",
        "Organization",
        "Country",
        "Sector",
        "Document_Type",
        "Publication_Date",
        "Source_URL",
        "Document_Language",
        "Passage",
    ]
    metadata = codings[
        [column for column in metadata_columns if column in codings.columns]
    ].drop_duplicates("Unit_ID")

    summaries = []
    for unit_id, group in codings.groupby("Unit_ID"):
        domains = [normalise_text(value) for value in group["Governance_Domain"]]
        domains = [value for value in domains if value]
        levels = pd.to_numeric(group["Evidence_Level"], errors="coerce").dropna()
        domain_agreement = len(set(domains)) == 1 and len(domains) >= 2
        level_agreement = levels.nunique() == 1 and len(levels) >= 2
        summaries.append(
            {
                "Unit_ID": unit_id,
                "Coder_Domains": " | ".join(
                    f"{row.Coder_ID}: {row.Governance_Domain}"
                    for row in group.itertuples()
                ),
                "Coder_Evidence_Levels": " | ".join(
                    f"{row.Coder_ID}: {row.Evidence_Level}"
                    for row in group.itertuples()
                ),
                "Final_Governance_Domain": domains[0] if domain_agreement else "",
                "Final_Evidence_Level": int(levels.iloc[0]) if level_agreement else pd.NA,
                "Adjudication_Rationale": "Agreed by coders"
                if domain_agreement and level_agreement
                else "",
                "Adjudicator_ID": "",
                "Adjudicated_At_UTC": "",
            }
        )
    return metadata.merge(pd.DataFrame(summaries), on="Unit_ID", how="right")


def expert_template(manual: pd.DataFrame) -> pd.DataFrame:
    base = manual[
        ["Indicator_ID", "Governance_Domain", "Indicator_Name"]
    ].copy()
    base.insert(0, "Reviewer_Expertise", "")
    base.insert(0, "Reviewer_ID", "")
    for column in RATING_COLUMNS:
        base[column] = pd.NA
    base["Comments"] = ""
    return base


def cvi_summary(expert_data: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    working = expert_data.copy()
    for column in RATING_COLUMNS:
        working[column] = pd.to_numeric(working[column], errors="coerce")

    rows = []
    for indicator_id, group in working.groupby("Indicator_ID", dropna=False):
        row = {
            "Indicator_ID": indicator_id,
            "Governance_Domain": group["Governance_Domain"].dropna().iloc[0]
            if group["Governance_Domain"].notna().any()
            else "",
            "Indicator_Name": group["Indicator_Name"].dropna().iloc[0]
            if group["Indicator_Name"].notna().any()
            else "",
            "Reviewers": group["Reviewer_ID"].replace("", pd.NA).nunique(),
        }
        for column in RATING_COLUMNS:
            valid = group[column].dropna()
            row[f"I_CVI_{column}"] = round(float((valid >= 3).mean()), 3) if len(valid) else np.nan
            row[f"Mean_{column}"] = round(float(valid.mean()), 2) if len(valid) else np.nan
        rows.append(row)

    summary = pd.DataFrame(rows)
    cvi_columns = [column for column in summary if column.startswith("I_CVI_")]
    scale_cvi = float(summary[cvi_columns].mean().mean()) if not summary.empty else np.nan
    return summary, scale_cvi


def project_workbook() -> bytes:
    sheets = {
        "Coding Manual": st.session_state.aig_manual,
        "Document Corpus": st.session_state.aig_corpus,
        "Pilot Sample": st.session_state.aig_pilot,
        "Change Log": st.session_state.aig_change_log,
    }
    if not st.session_state.aig_adjudicated.empty:
        sheets["Adjudicated Coding"] = st.session_state.aig_adjudicated
    return dataframes_to_excel_bytes(sheets)


def import_project_workbook(uploaded_file) -> None:
    workbook = pd.ExcelFile(uploaded_file)
    mappings = {
        "Coding Manual": "aig_manual",
        "Document Corpus": "aig_corpus",
        "Pilot Sample": "aig_pilot",
        "Change Log": "aig_change_log",
        "Adjudicated Coding": "aig_adjudicated",
    }
    for sheet, state_key in mappings.items():
        if sheet in workbook.sheet_names:
            st.session_state[state_key] = pd.read_excel(workbook, sheet_name=sheet)


def evidence_matrix(final_coding: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    working = final_coding.copy()
    if "Final_Governance_Domain" in working.columns:
        working["Governance_Domain"] = working["Final_Governance_Domain"]
    if "Final_Evidence_Level" in working.columns:
        working["Evidence_Level"] = working["Final_Evidence_Level"]

    working["Evidence_Level"] = pd.to_numeric(
        working["Evidence_Level"], errors="coerce"
    )
    working = working.dropna(
        subset=["Organization", "Governance_Domain", "Evidence_Level"]
    )
    working["Evidence_Level"] = working["Evidence_Level"].astype(int)

    counts = pd.crosstab(
        [working["Organization"], working["Governance_Domain"]],
        working["Evidence_Level"],
    ).reset_index()
    for level, label in EVIDENCE_LEVELS.items():
        if level not in counts.columns:
            counts[level] = 0
        counts.rename(columns={level: f"Level_{level}_{label}"}, inplace=True)

    level_columns = [f"Level_{level}_{label}" for level, label in EVIDENCE_LEVELS.items()]
    evidence_columns = [
        f"Level_{level}_{label}"
        for level, label in EVIDENCE_LEVELS.items()
        if level > 0
    ]
    counts["Total_Coded_Units"] = counts[level_columns].sum(axis=1)
    counts["Total_Coded_Claims"] = counts[evidence_columns].sum(axis=1)
    for column in level_columns:
        counts[f"Percent_{column}"] = (
            counts[column] / counts["Total_Coded_Units"] * 100
        ).round(1)

    coverage_index = pd.MultiIndex.from_product(
        [
            sorted(working["Organization"].astype(str).unique()),
            GOVERNANCE_DOMAINS,
        ],
        names=["Organization", "Governance_Domain"],
    ).to_frame(index=False)
    coverage = coverage_index.merge(
        counts[[
            "Organization",
            "Governance_Domain",
            "Total_Coded_Units",
            "Total_Coded_Claims",
        ]],
        on=["Organization", "Governance_Domain"],
        how="left",
    )
    coverage["Total_Coded_Units"] = coverage["Total_Coded_Units"].fillna(0).astype(int)
    coverage["Total_Coded_Claims"] = coverage["Total_Coded_Claims"].fillna(0).astype(int)
    coverage["Public_Evidence_Status"] = np.where(
        coverage["Total_Coded_Claims"] > 0,
        "Public claim or evidence coded",
        "No public claim or evidence located in the coded corpus",
    )
    return counts, coverage


initialise_state()

st.title("AI Governance Evidence Validation")
st.caption(
    "A source traceable research workspace for one comparative framework content analysis. "
    "The page supports coding and validation but does not automatically judge whether an "
    "organisation is ethical, compliant or trustworthy."
)

with st.sidebar:
    st.header("Project controls")
    project_upload = st.file_uploader(
        "Restore project workbook",
        type=["xlsx"],
        key="project_restore",
    )
    if project_upload is not None and st.button("Restore workbook"):
        try:
            import_project_workbook(project_upload)
            st.success("Project workbook restored.")
            st.rerun()
        except Exception as exc:
            st.error(f"The workbook could not be restored: {exc}")

    st.download_button(
        "Download project workbook",
        data=project_workbook(),
        file_name="AI_Governance_Validation_Project.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    st.divider()
    st.write("**Current status**")
    st.write(f"Manual version: {st.session_state.aig_manual_version}")
    st.write(f"Manual frozen: {'Yes' if st.session_state.aig_manual_frozen else 'No'}")
    st.write(f"Corpus units: {len(st.session_state.aig_corpus):,}")
    st.write(f"Pilot units: {len(st.session_state.aig_pilot):,}")
    st.write(f"Logged changes: {len(st.session_state.aig_change_log):,}")


overview_tab, manual_tab, corpus_tab, coder_tab, reliability_tab, expert_tab, change_tab, matrix_tab = st.tabs(
    [
        "Overview",
        "Coding manual",
        "Corpus and pilot",
        "Coder workspace",
        "Reliability",
        "Expert review",
        "Revision log",
        "Evidence matrix",
    ]
)


with overview_tab:
    st.subheader("Single analysis workflow")
    st.write(
        "This page supports one structured comparative content analysis. Reliability "
        "statistics and expert ratings validate the research instrument; they are not "
        "additional organisational outcome analyses."
    )
    steps = pd.DataFrame(
        [
            [1, "Define", "Complete the coding manual and evidence rules."],
            [2, "Build corpus", "Import source linked corporate document passages."],
            [3, "Pilot", "Select approximately 10 percent of coding units using a reproducible seed."],
            [4, "Code independently", "Two coders complete separate files without seeing each other's decisions."],
            [5, "Test reliability", "Calculate domain agreement, weighted kappa and ordinal alpha."],
            [6, "Validate", "Six to eight experts evaluate relevance, clarity and observability."],
            [7, "Revise and freeze", "Log every change and freeze the manual before full coding."],
            [8, "Analyse", "Create the final claim to evidence matrix across organisations and domains."],
        ],
        columns=["Step", "Stage", "Required action"],
    )
    st.dataframe(steps, use_container_width=True, hide_index=True)

    st.subheader("Evidence level rules")
    level_rows = pd.DataFrame(
        [
            [0, "No public evidence located", "The defined source set contains no explicit evidence for this organisation, year and governance domain."],
            [1, "Aspirational", "A principle or commitment is stated without an implementation mechanism."],
            [2, "Procedural", "A role, policy, committee, process or review procedure is specified."],
            [3, "Implemented", "Public evidence indicates that the procedure has been applied."],
            [4, "Verified", "Independent assurance, certification, audit evidence or externally verifiable results are provided."],
        ],
        columns=["Level", "Label", "Decision rule"],
    )
    st.dataframe(level_rows, use_container_width=True, hide_index=True)
    st.warning(
        "No public evidence located does not prove that an internal control is absent. "
        "Report findings as public verifiability, not as a definitive assessment of actual practice."
    )


with manual_tab:
    st.subheader("Detailed coding manual")
    first, second, third = st.columns([1, 1, 1])
    with first:
        manual_version = st.text_input(
            "Manual version",
            value=st.session_state.aig_manual_version,
        )
    with second:
        manual_frozen = st.checkbox(
            "Freeze manual for full coding",
            value=st.session_state.aig_manual_frozen,
            help="Freeze only after pilot reliability, expert review and documented revision.",
        )
    with third:
        manual_upload = st.file_uploader(
            "Replace manual from CSV or Excel",
            type=["csv", "xlsx"],
            key="manual_upload",
        )

    if manual_upload is not None and st.button("Import coding manual"):
        try:
            imported_manual = read_uploaded_table(manual_upload)
            required = ["Indicator_ID", "Governance_Domain", "Indicator_Name"]
            missing = missing_required_columns(imported_manual, required)
            if missing:
                st.error(f"Missing columns: {', '.join(missing)}")
            else:
                st.session_state.aig_manual = imported_manual
                st.success("Coding manual imported.")
                st.rerun()
        except Exception as exc:
            st.error(f"The coding manual could not be imported: {exc}")

    edited_manual = st.data_editor(
        st.session_state.aig_manual,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        disabled=manual_frozen,
        key="manual_editor",
        column_config={
            "Governance_Domain": st.column_config.SelectboxColumn(
                options=GOVERNANCE_DOMAINS,
                required=True,
            ),
            "Status": st.column_config.SelectboxColumn(
                options=["Draft", "Pilot", "Revised", "Frozen", "Retired"],
            ),
        },
    )

    if st.button("Save coding manual", type="primary", disabled=manual_frozen):
        edited_manual["Manual_Version"] = manual_version
        edited_manual["Status"] = edited_manual["Status"].fillna("Draft")
        st.session_state.aig_manual = edited_manual
        st.session_state.aig_manual_version = manual_version
        st.session_state.aig_manual_frozen = manual_frozen
        st.success("Coding manual saved in this session.")

    if manual_frozen != st.session_state.aig_manual_frozen:
        st.session_state.aig_manual_frozen = manual_frozen
        st.session_state.aig_manual_version = manual_version

    st.download_button(
        "Download coding manual",
        data=dataframe_to_csv_bytes(st.session_state.aig_manual),
        file_name=f"AI_Governance_Coding_Manual_v{manual_version}.csv",
        mime="text/csv",
    )


with corpus_tab:
    st.subheader("Document corpus and pilot sample")
    template = empty_corpus()
    template.loc[0] = [
        "",
        "DOC_001",
        "Example organisation",
        "Example country",
        "Example sector",
        "Responsible AI policy",
        "2026-01-01",
        "https://example.org/source",
        "English",
        "Paste one source linked governance claim or evidence passage here.",
        "Leadership accountability",
        "Optional researcher note",
    ]
    st.download_button(
        "Download corpus template",
        data=dataframe_to_csv_bytes(template),
        file_name="AI_Governance_Corpus_Template.csv",
        mime="text/csv",
    )

    corpus_upload = st.file_uploader(
        "Upload document corpus",
        type=["csv", "xlsx"],
        key="corpus_upload",
    )
    if corpus_upload is not None and st.button("Import corpus"):
        try:
            imported_corpus = read_uploaded_table(corpus_upload)
            required = [
                "Document_ID",
                "Organization",
                "Country",
                "Sector",
                "Document_Type",
                "Source_URL",
                "Passage",
            ]
            missing = missing_required_columns(imported_corpus, required)
            if missing:
                st.error(f"Missing columns: {', '.join(missing)}")
            else:
                imported_corpus = add_unit_ids(imported_corpus)
                imported_corpus = align_columns(imported_corpus, CORPUS_COLUMNS)
                st.session_state.aig_corpus = imported_corpus
                st.success(f"Imported {len(imported_corpus):,} coding units.")
                st.rerun()
        except Exception as exc:
            st.error(f"The corpus could not be imported: {exc}")

    corpus = st.session_state.aig_corpus
    if corpus.empty:
        st.info("Import a corpus to generate a pilot sample.")
    else:
        st.dataframe(corpus.head(100), use_container_width=True, hide_index=True)
        st.caption(f"Showing up to 100 of {len(corpus):,} coding units.")

        left, middle, right = st.columns(3)
        with left:
            pilot_percent = st.slider(
                "Pilot percentage",
                min_value=5,
                max_value=25,
                value=10,
                step=1,
            )
        with middle:
            minimum_units = st.number_input(
                "Minimum pilot units",
                min_value=1,
                value=min(30, len(corpus)),
                step=1,
            )
        with right:
            random_seed = st.number_input(
                "Random seed",
                min_value=0,
                value=2026,
                step=1,
            )

        available_strata = [
            column
            for column in [
                "Organization",
                "Country",
                "Sector",
                "Document_Type",
                "Proposed_Governance_Domain",
            ]
            if column in corpus.columns
        ]
        strata = st.multiselect(
            "Stratify pilot across",
            options=available_strata,
            default=[
                column
                for column in ["Organization", "Document_Type"]
                if column in available_strata
            ],
        )

        if st.button("Generate reproducible pilot sample", type="primary"):
            pilot = stratified_pilot_sample(
                corpus,
                fraction=pilot_percent / 100,
                minimum_units=int(minimum_units),
                strata_columns=strata,
                seed=int(random_seed),
            )
            st.session_state.aig_pilot = pilot
            st.success(f"Generated a pilot sample of {len(pilot):,} coding units.")

    pilot = st.session_state.aig_pilot
    if not pilot.empty:
        st.markdown("#### Pilot sample")
        st.dataframe(pilot, use_container_width=True, hide_index=True)
        st.download_button(
            "Download blinded pilot file",
            data=dataframe_to_csv_bytes(pilot),
            file_name="AI_Governance_Blinded_Pilot.csv",
            mime="text/csv",
        )


with coder_tab:
    st.subheader("Independent coder workspace")
    st.info(
        "Each coder should open a separate session, use a unique coder ID and download "
        "their own completed file. Do not upload another coder's decisions into this tab."
    )

    source_choice = st.radio(
        "Coding source",
        ["Use pilot sample from this session", "Upload a blinded coding file"],
        horizontal=True,
    )
    coding_source = st.session_state.aig_pilot.copy()
    if source_choice == "Upload a blinded coding file":
        coding_upload = st.file_uploader(
            "Upload blinded pilot or full corpus",
            type=["csv", "xlsx"],
            key="blinded_coding_upload",
        )
        if coding_upload is not None:
            try:
                coding_source = read_uploaded_table(coding_upload)
                coding_source = add_unit_ids(coding_source)
            except Exception as exc:
                st.error(f"The coding file could not be read: {exc}")
                coding_source = pd.DataFrame()

    if coding_source.empty:
        st.warning("Generate or upload a blinded coding file first.")
    else:
        first, second = st.columns(2)
        with first:
            coder_id = st.text_input("Coder ID", placeholder="CODER_01")
        with second:
            coder_manual_version = st.text_input(
                "Coding manual version used",
                value=st.session_state.aig_manual_version,
            )

        coding_frame = align_columns(coding_source, CODING_COLUMNS)
        proposed_domains = coding_frame["Proposed_Governance_Domain"].astype("string")
        missing_domains = coding_frame["Governance_Domain"].isna() | (
            coding_frame["Governance_Domain"].astype("string").str.strip() == ""
        )
        coding_frame.loc[missing_domains, "Governance_Domain"] = proposed_domains[
            missing_domains
        ]
        editable_columns = [
            "Unit_ID",
            "Organization",
            "Document_Type",
            "Source_URL",
            "Passage",
            "Governance_Domain",
            "Evidence_Level",
            "Decision_Rationale",
            "Confidence",
            "Ambiguous",
        ]
        coding_editor = st.data_editor(
            coding_frame[editable_columns],
            use_container_width=True,
            hide_index=True,
            disabled=[
                "Unit_ID",
                "Organization",
                "Document_Type",
                "Source_URL",
                "Passage",
            ],
            key="independent_coding_editor",
            column_config={
                "Governance_Domain": st.column_config.SelectboxColumn(
                    options=GOVERNANCE_DOMAINS,
                    required=True,
                ),
                "Evidence_Level": st.column_config.SelectboxColumn(
                    options=list(EVIDENCE_LEVELS.keys()),
                    required=True,
                    help="0 No public evidence located, 1 Aspirational, 2 Procedural, 3 Implemented, 4 Verified",
                ),
                "Confidence": st.column_config.SelectboxColumn(
                    options=[1, 2, 3, 4, 5],
                ),
                "Ambiguous": st.column_config.SelectboxColumn(
                    options=["No", "Yes"],
                ),
                "Source_URL": st.column_config.LinkColumn(),
                "Passage": st.column_config.TextColumn(width="large"),
                "Decision_Rationale": st.column_config.TextColumn(width="large"),
            },
        )

        base_columns = [
            column
            for column in coding_frame.columns
            if column == "Unit_ID" or column not in editable_columns
        ]
        completed = coding_frame[base_columns].merge(
            coding_editor,
            on="Unit_ID",
            how="right",
        )
        completed["Coder_ID"] = coder_id.strip()
        completed["Manual_Version"] = coder_manual_version.strip()
        completed["Coded_At_UTC"] = utc_now()
        completed["Evidence_Level"] = pd.to_numeric(
            completed["Evidence_Level"], errors="coerce"
        )
        completed["Evidence_Label"] = completed["Evidence_Level"].map(EVIDENCE_LEVELS)
        completed = align_columns(completed, CODING_COLUMNS)

        complete_mask = (
            completed["Governance_Domain"].notna()
            & completed["Evidence_Level"].notna()
            & completed["Decision_Rationale"].fillna("").astype(str).str.strip().ne("")
        )
        st.progress(float(complete_mask.mean()), text=f"{int(complete_mask.sum())} of {len(completed)} units complete")

        if not coder_id.strip():
            st.warning("Enter a coder ID before downloading the completed file.")
        st.download_button(
            "Download independent coding file",
            data=dataframe_to_csv_bytes(completed),
            file_name=f"AI_Governance_Coding_{coder_id.strip() or 'CODER_ID_REQUIRED'}.csv",
            mime="text/csv",
            disabled=not coder_id.strip(),
        )


with reliability_tab:
    st.subheader("Intercoder reliability and adjudication")
    coding_uploads = st.file_uploader(
        "Upload at least two independent coding files",
        type=["csv", "xlsx"],
        accept_multiple_files=True,
        key="reliability_uploads",
    )

    combined_codings = pd.DataFrame()
    if coding_uploads:
        frames = []
        for uploaded in coding_uploads:
            try:
                frames.append(read_uploaded_table(uploaded))
            except Exception as exc:
                st.error(f"Could not read {uploaded.name}: {exc}")
        if frames:
            combined_codings = pd.concat(frames, ignore_index=True)
            required = [
                "Unit_ID",
                "Coder_ID",
                "Governance_Domain",
                "Evidence_Level",
            ]
            missing = missing_required_columns(combined_codings, required)
            if missing:
                st.error(f"Missing columns: {', '.join(missing)}")
                combined_codings = pd.DataFrame()
            else:
                combined_codings["Evidence_Level"] = pd.to_numeric(
                    combined_codings["Evidence_Level"], errors="coerce"
                )
                combined_codings = combined_codings.dropna(
                    subset=["Unit_ID", "Coder_ID", "Governance_Domain", "Evidence_Level"]
                )
                duplicate_mask = combined_codings.duplicated(
                    ["Unit_ID", "Coder_ID"], keep=False
                )
                if duplicate_mask.any():
                    st.error(
                        "Duplicate Unit ID and Coder ID combinations were found. "
                        "Resolve them before calculating reliability."
                    )
                    st.dataframe(
                        combined_codings.loc[duplicate_mask],
                        use_container_width=True,
                        hide_index=True,
                    )
                    combined_codings = pd.DataFrame()

    if not combined_codings.empty:
        coder_count = combined_codings["Coder_ID"].astype(str).nunique()
        unit_count = combined_codings["Unit_ID"].astype(str).nunique()
        first, second = st.columns(2)
        first.metric("Coders", coder_count)
        second.metric("Unique units", unit_count)

        if coder_count < 2:
            st.warning("At least two different coder IDs are required.")
        else:
            pairwise = pairwise_reliability(combined_codings)
            st.markdown("#### Pairwise reliability")
            st.dataframe(pairwise, use_container_width=True, hide_index=True)

            if krippendorff is None:
                st.warning(
                    "Install the krippendorff package to calculate ordinal and nominal alpha. "
                    "Weighted Cohen's kappa is still available."
                )
            else:
                try:
                    evidence_alpha, domain_alpha = krippendorff_results(combined_codings)
                    alpha_left, alpha_right = st.columns(2)
                    alpha_left.metric(
                        "Ordinal alpha for evidence level",
                        "Not estimable" if np.isnan(evidence_alpha) else f"{evidence_alpha:.3f}",
                    )
                    alpha_right.metric(
                        "Nominal alpha for governance domain",
                        "Not estimable" if np.isnan(domain_alpha) else f"{domain_alpha:.3f}",
                    )
                except Exception as exc:
                    st.warning(f"Krippendorff's alpha could not be estimated: {exc}")

            disagreements = disagreement_table(combined_codings)
            st.markdown("#### Coding disagreements")
            st.dataframe(disagreements, use_container_width=True, hide_index=True)
            st.download_button(
                "Download disagreement report",
                data=dataframe_to_csv_bytes(disagreements),
                file_name="AI_Governance_Coding_Disagreements.csv",
                mime="text/csv",
            )

            adjudication = adjudication_template(combined_codings)
            st.markdown("#### Adjudication workspace")
            st.caption(
                "Agreements are prefilled. Resolve disagreements using the frozen manual and "
                "record a rationale. Do not alter the manual during full coding without a logged version change."
            )
            adjudication_editor = st.data_editor(
                adjudication,
                use_container_width=True,
                hide_index=True,
                disabled=[
                    "Unit_ID",
                    "Document_ID",
                    "Organization",
                    "Country",
                    "Sector",
                    "Document_Type",
                    "Publication_Date",
                    "Source_URL",
                    "Document_Language",
                    "Passage",
                    "Coder_Domains",
                    "Coder_Evidence_Levels",
                ],
                key="adjudication_editor",
                column_config={
                    "Final_Governance_Domain": st.column_config.SelectboxColumn(
                        options=GOVERNANCE_DOMAINS,
                    ),
                    "Final_Evidence_Level": st.column_config.SelectboxColumn(
                        options=list(EVIDENCE_LEVELS.keys()),
                    ),
                    "Source_URL": st.column_config.LinkColumn(),
                    "Passage": st.column_config.TextColumn(width="large"),
                    "Adjudication_Rationale": st.column_config.TextColumn(width="large"),
                },
            )
            if st.button("Save adjudicated coding", type="primary"):
                save_frame = adjudication_editor.copy()
                timestamp = utc_now()
                fill_time = (
                    save_frame["Adjudicated_At_UTC"].fillna("").astype(str).str.strip() == ""
                ) & save_frame["Final_Evidence_Level"].notna()
                save_frame.loc[fill_time, "Adjudicated_At_UTC"] = timestamp
                st.session_state.aig_adjudicated = save_frame
                st.success("Adjudicated coding saved in this session.")

            st.download_button(
                "Download adjudication file",
                data=dataframe_to_csv_bytes(adjudication_editor),
                file_name="AI_Governance_Adjudicated_Coding.csv",
                mime="text/csv",
            )


with expert_tab:
    st.subheader("Expert content validation")
    st.write(
        "Invite six to eight experts to rate every indicator from 1, not relevant or unclear, "
        "to 4, highly relevant or very clear. Each expert completes a separate copy."
    )
    expert_form = expert_template(st.session_state.aig_manual)
    st.download_button(
        "Download expert review template",
        data=dataframe_to_csv_bytes(expert_form),
        file_name=f"AI_Governance_Expert_Review_v{st.session_state.aig_manual_version}.csv",
        mime="text/csv",
    )

    expert_uploads = st.file_uploader(
        "Upload completed expert review files",
        type=["csv", "xlsx"],
        accept_multiple_files=True,
        key="expert_uploads",
    )
    if expert_uploads:
        expert_frames = []
        for uploaded in expert_uploads:
            try:
                expert_frames.append(read_uploaded_table(uploaded))
            except Exception as exc:
                st.error(f"Could not read {uploaded.name}: {exc}")
        if expert_frames:
            expert_data = pd.concat(expert_frames, ignore_index=True)
            required = [
                "Reviewer_ID",
                "Indicator_ID",
                "Governance_Domain",
                "Indicator_Name",
            ] + RATING_COLUMNS
            missing = missing_required_columns(expert_data, required)
            if missing:
                st.error(f"Missing columns: {', '.join(missing)}")
            else:
                summary, scale_cvi = cvi_summary(expert_data)
                reviewer_count = expert_data["Reviewer_ID"].replace("", pd.NA).nunique()
                metric_left, metric_right = st.columns(2)
                metric_left.metric("Experts represented", reviewer_count)
                metric_right.metric(
                    "Scale content validity index",
                    "Not estimable" if np.isnan(scale_cvi) else f"{scale_cvi:.3f}",
                )
                st.dataframe(summary, use_container_width=True, hide_index=True)
                st.caption(
                    "An item content validity index of approximately 0.78 or higher is commonly "
                    "used as a review guide with six or more experts. Decisions must also consider comments and theory."
                )
                st.download_button(
                    "Download expert validation summary",
                    data=dataframe_to_csv_bytes(summary),
                    file_name="AI_Governance_Expert_Validation_Summary.csv",
                    mime="text/csv",
                )


with change_tab:
    st.subheader("Framework revision and version history")
    st.write(
        "Record changes arising from pilot disagreements, expert comments or theoretical review. "
        "Create a new manual version whenever a decision rule or indicator meaning changes."
    )
    change_editor = st.data_editor(
        st.session_state.aig_change_log,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key="change_log_editor",
        column_config={
            "Decision": st.column_config.SelectboxColumn(
                options=["Pending", "Accepted", "Modified", "Rejected"],
            ),
            "Date_UTC": st.column_config.TextColumn(),
        },
    )
    if st.button("Save revision log", type="primary"):
        saved_log = align_columns(change_editor, CHANGE_LOG_COLUMNS)
        missing_ids = saved_log["Change_ID"].fillna("").astype(str).str.strip() == ""
        for index in saved_log.index[missing_ids]:
            saved_log.at[index, "Change_ID"] = f"CHG_{index + 1:03d}"
        missing_dates = saved_log["Date_UTC"].fillna("").astype(str).str.strip() == ""
        saved_log.loc[missing_dates, "Date_UTC"] = utc_now()
        st.session_state.aig_change_log = saved_log
        st.success("Revision log saved in this session.")

    st.download_button(
        "Download revision log",
        data=dataframe_to_csv_bytes(st.session_state.aig_change_log),
        file_name="AI_Governance_Framework_Revision_Log.csv",
        mime="text/csv",
    )


with matrix_tab:
    st.subheader("Final claim to evidence matrix")
    source = st.radio(
        "Final coding source",
        ["Use adjudicated coding from this session", "Upload final adjudicated coding"],
        horizontal=True,
    )
    final_coding = st.session_state.aig_adjudicated.copy()
    if source == "Upload final adjudicated coding":
        final_upload = st.file_uploader(
            "Upload final coding file",
            type=["csv", "xlsx"],
            key="final_coding_upload",
        )
        if final_upload is not None:
            try:
                final_coding = read_uploaded_table(final_upload)
            except Exception as exc:
                st.error(f"The final coding file could not be read: {exc}")
                final_coding = pd.DataFrame()

    if final_coding.empty:
        st.info("Save or upload final adjudicated coding to create the evidence matrix.")
    else:
        required_alternatives = {
            "Organization": ["Organization"],
            "Governance domain": ["Final_Governance_Domain", "Governance_Domain"],
            "Evidence level": ["Final_Evidence_Level", "Evidence_Level"],
        }
        missing_groups = [
            label
            for label, alternatives in required_alternatives.items()
            if not any(column in final_coding.columns for column in alternatives)
        ]
        if missing_groups:
            st.error(f"Missing required information: {', '.join(missing_groups)}")
        else:
            counts, coverage = evidence_matrix(final_coding)
            st.markdown("#### Evidence distribution by organisation and governance domain")
            st.dataframe(counts, use_container_width=True, hide_index=True)
            st.markdown("#### Governance domain coverage")
            st.dataframe(coverage, use_container_width=True, hide_index=True)

            detail_columns = [
                column
                for column in [
                    "Unit_ID",
                    "Organization",
                    "Country",
                    "Sector",
                    "Document_Type",
                    "Publication_Date",
                    "Source_URL",
                    "Passage",
                    "Final_Governance_Domain",
                    "Final_Evidence_Level",
                    "Adjudication_Rationale",
                ]
                if column in final_coding.columns
            ]
            st.markdown("#### Source linked coding evidence")
            st.dataframe(
                final_coding[detail_columns],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Source_URL": st.column_config.LinkColumn(),
                },
            )

            matrix_workbook = dataframes_to_excel_bytes(
                {
                    "Evidence Distribution": counts,
                    "Domain Coverage": coverage,
                    "Source Linked Evidence": final_coding,
                }
            )
            st.download_button(
                "Download final evidence workbook",
                data=matrix_workbook,
                file_name="AI_Governance_Final_Evidence_Matrix.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            st.warning(
                "The matrix reports the public evidence located in the defined corpus. "
                "It must not be described as a legal compliance score, an ethical ranking, "
                "a measure of actual internal practice or a prediction of stakeholder trust."
            )


st.divider()
st.caption(
    "Research prototype. Preserve source links, coding files, manual versions, expert reviews "
    "and revision records with the final article materials."
)
