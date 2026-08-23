import re

import pandas as pd
import streamlit as st

from utils.excel_export import dataframes_to_excel_bytes


def _safe_filename(value):
    text = re.sub(
        r"[^A-Za-z0-9._-]+",
        "_",
        str(value or "export").strip(),
    )
    return text.strip("_") or "export"


def dataframe_csv_bytes(frame):
    if frame is None:
        frame = pd.DataFrame()

    current = (
        frame.copy()
        if isinstance(frame, pd.DataFrame)
        else pd.DataFrame(frame)
    )

    return current.to_csv(
        index=False
    ).encode(
        "utf-8-sig"
    )


def dataframe_xlsx_bytes(
    frame,
    *,
    sheet_name="Data",
    metadata=None,
):
    return dataframes_to_excel_bytes(
        [
            (
                sheet_name,
                frame,
            )
        ],
        metadata=metadata,
    )


def render_section_export(
    *,
    base_name,
    data=None,
    figure=None,
    sheet_name="Data",
    metadata=None,
    image_width=1600,
    image_height=900,
    show_label=True,
):
    """
    Client-friendly per-section exports.

    Excel + CSV:
        direct Streamlit download buttons.

    PNG:
        uses Plotly's browser-side camera/download control.
        This avoids a server-side Chrome/Kaleido dependency and is
        more reliable on hosted Streamlit deployments.
    """
    safe = _safe_filename(
        base_name
    )

    if show_label:
        st.caption(
            "Client export"
        )

    columns = st.columns(
        [
            1,
            1,
            2.2,
            2,
        ]
    )

    if data is not None:
        current = (
            data.copy()
            if isinstance(
                data,
                pd.DataFrame,
            )
            else pd.DataFrame(
                data
            )
        )

        xlsx_bytes = (
            dataframe_xlsx_bytes(
                current,
                sheet_name=sheet_name,
                metadata=metadata,
            )
        )

        csv_bytes = (
            dataframe_csv_bytes(
                current
            )
        )

        with columns[0]:
            st.download_button(
                "Excel",
                data=xlsx_bytes,
                file_name=f"{safe}.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                use_container_width=True,
                key=f"xlsx_{safe}",
            )

        with columns[1]:
            st.download_button(
                "CSV",
                data=csv_bytes,
                file_name=f"{safe}.csv",
                mime="text/csv",
                use_container_width=True,
                key=f"csv_{safe}",
            )
    else:
        with columns[0]:
            st.button(
                "Excel",
                disabled=True,
                use_container_width=True,
                key=f"xlsx_disabled_{safe}",
            )

        with columns[1]:
            st.button(
                "CSV",
                disabled=True,
                use_container_width=True,
                key=f"csv_disabled_{safe}",
            )

    with columns[2]:
        if figure is not None:
            st.caption(
                "PNG image: hover over the chart and click the 📷 camera icon."
            )
        else:
            st.caption(
                "This section is data-only."
            )
