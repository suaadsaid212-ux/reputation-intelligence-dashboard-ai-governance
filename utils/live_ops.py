from datetime import datetime

import pandas as pd
import streamlit as st


STATUS_COLORS = {
    "LIVE": ("#0F766E", "#CCFBF1"),
    "CACHED": ("#1D4ED8", "#DBEAFE"),
    "ON-DEMAND": ("#6D28D9", "#EDE9FE"),
    "PROXY": ("#B45309", "#FEF3C7"),
    "PROTOTYPE": ("#B45309", "#FEF3C7"),
    "CONNECTOR-READY": ("#475569", "#E2E8F0"),
    "UNAVAILABLE": ("#B91C1C", "#FEE2E2"),
}


def now_local():
    return datetime.now().astimezone()


def format_local_time(value=None):
    value = value or now_local()
    return value.strftime("%d %b %Y • %H:%M:%S %Z")


def render_live_status(
    sources,
    *,
    note="",
    refreshed_at=None,
):
    """
    sources: list of (label, status) tuples.
    Status should be one of LIVE, CACHED, ON-DEMAND,
    PROXY, PROTOTYPE, CONNECTOR-READY, UNAVAILABLE.
    """
    refreshed_at = refreshed_at or now_local()

    badge_html = []

    for label, status in sources:
        status = str(status).upper()
        fg, bg = STATUS_COLORS.get(
            status,
            ("#334155", "#E2E8F0"),
        )

        badge_html.append(
            (
                f'<span class="ti-source-pill">'
                f'<span class="ti-source-name">{label}</span>'
                f'<span class="ti-source-status" '
                f'style="color:{fg};background:{bg};">{status}</span>'
                f'</span>'
            )
        )

    note_html = (
        f'<div class="ti-status-note">{note}</div>'
        if note
        else ""
    )

    html = (
        f'<div class="ti-statusbar">'
        f'  <div class="ti-status-left">'
        f'    <span class="ti-live-dot"></span>'
        f'    <span class="ti-status-title">Intelligence Operations</span>'
        f'    {"".join(badge_html)}'
        f'  </div>'
        f'  <div class="ti-status-time">'
        f'    Page refreshed {format_local_time(refreshed_at)}'
        f'  </div>'
        f'</div>'
        f'{note_html}'
    )

    st.markdown(
        html,
        unsafe_allow_html=True,
    )


def source_health_frame(rows):
    """
    Build a simple, consistently ordered source-health dataframe.
    Each row can include:
    Source, Status, Freshness, Coverage, Notes.
    """
    columns = [
        "Source",
        "Status",
        "Freshness",
        "Coverage",
        "Notes",
    ]

    frame = pd.DataFrame(
        rows,
        columns=columns,
    )

    return frame
