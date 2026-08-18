import math
import re
from collections import Counter

import pandas as pd
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from utils.social_utils import (
    PLATFORM_CATALOG,
    clean_text,
    collect_social_narratives,
    empty_posts_frame,
    safe_int,
    sentiment_label,
)


EXPANDED_PLATFORM_CATALOG = {
    **PLATFORM_CATALOG,
    "Bluesky": {
        "source_type": "Social network",
        "access_mode": "Live public Bluesky AppView API",
        "data_status": "Live public API",
        "geo_scope": "Global public posts; reliable user geography is usually unavailable",
        "language_scope": "Multilingual when post language metadata is available",
    },
    "Threads": {
        "source_type": "Social network",
        "access_mode": "Official Meta / Threads API access required",
        "data_status": "Connector planned",
        "geo_scope": "Depends on approved API fields and public account metadata",
        "language_scope": "Multilingual after connector setup",
    },
    "Facebook Public Pages": {
        "source_type": "Social network",
        "access_mode": "Meta Graph API and approved permissions required",
        "data_status": "Connector planned",
        "geo_scope": "Page-level geography where permitted",
        "language_scope": "Multilingual after connector setup",
    },
    "Telegram Public Channels": {
        "source_type": "Messaging / public channels",
        "access_mode": "Telegram API client credentials required",
        "data_status": "Connector planned",
        "geo_scope": "Channel-level only unless public metadata supports more",
        "language_scope": "Multilingual",
    },
    "Discord Public Communities": {
        "source_type": "Community / chat",
        "access_mode": "Bot or approved server access required",
        "data_status": "Connector planned",
        "geo_scope": "Server/community level; user geography generally unavailable",
        "language_scope": "Multilingual",
    },
    "Lemmy": {
        "source_type": "Decentralized forum",
        "access_mode": "Public instance APIs available; connector planned",
        "data_status": "Connector planned",
        "geo_scope": "Instance/community level",
        "language_scope": "Multilingual by instance/community",
    },
    "Medium / Public Blogs": {
        "source_type": "Publishing / blogs",
        "access_mode": "RSS or publisher-specific public feeds where available",
        "data_status": "Connector planned",
        "geo_scope": "Publisher/site level",
        "language_scope": "Multilingual",
    },
}


def fetch_bluesky_posts(query, limit=20):
    if not query:
        return empty_posts_frame()

    analyzer = SentimentIntensityAnalyzer()

    response = requests.get(
        "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts",
        params={"q": query, "limit": min(int(limit), 100)},
        headers={"Accept": "application/json"},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    rows = []

    for item in payload.get("posts", []):
        record = item.get("record", {}) or {}
        author = item.get("author", {}) or {}
        text = clean_text(record.get("text", ""))

        if not text:
            continue

        sentiment = analyzer.polarity_scores(text)["compound"]
        uri = item.get("uri", "")
        rkey = uri.rsplit("/", 1)[-1] if uri else ""
        handle = author.get("handle", "")
        url = (
            f"https://bsky.app/profile/{handle}/post/{rkey}"
            if handle and rkey
            else ""
        )
        langs = record.get("langs", []) or []

        rows.append(
            {
                "Platform": "Bluesky",
                "Source_Type": EXPANDED_PLATFORM_CATALOG["Bluesky"]["source_type"],
                "Title": text[:117] + "..." if len(text) > 120 else text,
                "Text": text,
                "Author": author.get("displayName") or handle,
                "Published_At": item.get("indexedAt")
                or record.get("createdAt", ""),
                "Engagement": safe_int(item.get("likeCount"))
                + safe_int(item.get("repostCount"))
                + safe_int(item.get("replyCount"))
                + safe_int(item.get("quoteCount")),
                "Sentiment": sentiment,
                "Sentiment_Label": sentiment_label(sentiment),
                "Url": url,
                "Data_Status": "Live public API",
                "Geo_Scope": EXPANDED_PLATFORM_CATALOG["Bluesky"]["geo_scope"],
                "Language": ", ".join(langs) if langs else "unknown",
            }
        )

    return pd.DataFrame(rows) if rows else empty_posts_frame()


def collect_expanded_social_narratives(
    query,
    selected_platforms,
    youtube_api_key="",
    limit_per_platform=20,
):
    selected_platforms = list(selected_platforms or [])

    core_platforms = [
        platform
        for platform in selected_platforms
        if platform in PLATFORM_CATALOG and platform != "Bluesky"
    ]

    posts, _, errors = collect_social_narratives(
        query=query,
        selected_platforms=core_platforms,
        youtube_api_key=youtube_api_key,
        limit_per_platform=limit_per_platform,
    )

    frames = [posts] if not posts.empty else []

    if "Bluesky" in selected_platforms:
        try:
            bluesky = fetch_bluesky_posts(
                query=query,
                limit=limit_per_platform,
            )
            if not bluesky.empty:
                frames.append(bluesky)
        except Exception as error:
            errors.append(f"Bluesky: {error}")

    if frames:
        combined = pd.concat(frames, ignore_index=True)
        combined = combined.drop_duplicates(
            subset=["Platform", "Title", "Url"],
            keep="first",
        )
    else:
        combined = empty_posts_frame()

    coverage = build_expanded_coverage(
        selected_platforms=selected_platforms,
        posts=combined,
        youtube_api_key=youtube_api_key,
    )

    return combined, coverage, errors


def build_expanded_coverage(
    selected_platforms,
    posts,
    youtube_api_key="",
):
    rows = []

    for platform in selected_platforms:
        meta = EXPANDED_PLATFORM_CATALOG.get(platform, {})

        platform_posts = (
            posts[posts["Platform"].eq(platform)]
            if not posts.empty
            else pd.DataFrame()
        )

        status = meta.get("data_status", "Unknown")

        if platform == "YouTube":
            if youtube_api_key and not platform_posts.empty:
                status = "Live API connected"
            elif youtube_api_key:
                status = "API connected; no matching rows"
            else:
                status = "Add YOUTUBE_API_KEY for live data"
        elif not platform_posts.empty:
            status = "Live rows loaded"
        elif status == "Live public API":
            status = "No rows returned or public endpoint unavailable"

        rows.append(
            {
                "Platform": platform,
                "Source Type": meta.get("source_type", ""),
                "Access Mode": meta.get("access_mode", ""),
                "Data Status": status,
                "Rows": int(len(platform_posts)),
                "Geographic Coverage": meta.get("geo_scope", ""),
                "Language Coverage": meta.get("language_scope", ""),
            }
        )

    return pd.DataFrame(rows)


def platform_comparison(posts):
    columns = [
        "Platform",
        "Mentions",
        "Mention Share %",
        "Engagement",
        "Engagement Share %",
        "Average Sentiment",
        "Negative Share %",
        "Platform Risk",
    ]

    if posts.empty:
        return pd.DataFrame(columns=columns)

    total_mentions = max(len(posts), 1)
    total_engagement = max(
        int(posts["Engagement"].fillna(0).sum()),
        1,
    )

    rows = []

    for platform, frame in posts.groupby("Platform"):
        mentions = len(frame)
        engagement = int(frame["Engagement"].fillna(0).sum())
        avg_sentiment = float(
            frame["Sentiment"].fillna(0).mean()
        )
        negative_share = float(
            frame["Sentiment"].lt(-0.05).mean() * 100
        )

        volume_score = min(100.0, mentions * 4.0)
        engagement_score = min(
            100.0,
            math.log1p(max(engagement, 0))
            / math.log1p(100000)
            * 100,
        )
        sentiment_pressure = max(
            0.0,
            min(100.0, (1 - avg_sentiment) * 50),
        )

        risk = round(
            0.45 * negative_share
            + 0.25 * volume_score
            + 0.20 * sentiment_pressure
            + 0.10 * engagement_score,
            2,
        )

        rows.append(
            {
                "Platform": platform,
                "Mentions": mentions,
                "Mention Share %": round(
                    mentions / total_mentions * 100,
                    2,
                ),
                "Engagement": engagement,
                "Engagement Share %": round(
                    engagement / total_engagement * 100,
                    2,
                ),
                "Average Sentiment": round(
                    avg_sentiment,
                    3,
                ),
                "Negative Share %": round(
                    negative_share,
                    2,
                ),
                "Platform Risk": min(100.0, risk),
            }
        )

    return (
        pd.DataFrame(rows)
        .sort_values(
            ["Platform Risk", "Mentions"],
            ascending=[False, False],
        )
        .reset_index(drop=True)
    )


def cross_platform_terms(posts, top_n=15):
    columns = [
        "Term",
        "Platforms",
        "Platform Count",
        "Frequency",
    ]

    if posts.empty:
        return pd.DataFrame(columns=columns)

    stopwords = {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "are",
        "was",
        "were",
        "has",
        "have",
        "but",
        "not",
        "you",
        "your",
        "its",
        "into",
        "about",
        "will",
        "can",
        "more",
        "new",
    }

    by_term = {}

    for platform, frame in posts.groupby("Platform"):
        text = " ".join(
            frame["Text"].fillna("").astype(str).tolist()
        ).lower()

        tokens = [
            token
            for token in re.findall(
                r"[a-z][a-z0-9\-]{2,}",
                text,
            )
            if token not in stopwords
            and not token.startswith("http")
        ]

        counts = Counter(tokens)

        for term, frequency in counts.items():
            item = by_term.setdefault(
                term,
                {"platforms": set(), "frequency": 0},
            )
            item["platforms"].add(platform)
            item["frequency"] += int(frequency)

    rows = [
        {
            "Term": term,
            "Platforms": ", ".join(
                sorted(values["platforms"])
            ),
            "Platform Count": len(values["platforms"]),
            "Frequency": values["frequency"],
        }
        for term, values in by_term.items()
        if len(values["platforms"]) >= 2
    ]

    if not rows:
        return pd.DataFrame(columns=columns)

    return (
        pd.DataFrame(rows)
        .sort_values(
            ["Platform Count", "Frequency"],
            ascending=False,
        )
        .head(top_n)
        .reset_index(drop=True)
    )
