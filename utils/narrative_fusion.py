import ipaddress
import math
import re
import socket
from collections import Counter
from datetime import datetime, timezone
from html import unescape
from urllib.parse import urljoin, urlparse

import feedparser
import pandas as pd
import requests

from utils.multilingual_content import (
    NEWS_PROFILES,
    detect_script_language,
    score_multilingual_sentiment,
    sentiment_label,
)


USER_AGENT = "TrustIntelAI-NarrativeFusion/0.1"

STOPWORDS = {
    "about", "after", "again", "against", "also", "amid", "and", "are",
    "because", "been", "being", "but", "can", "could", "from", "has",
    "have", "into", "its", "more", "new", "not", "now", "official", "our",
    "over", "said", "says", "that", "the", "their", "this", "through",
    "using", "was", "were", "what", "when", "where", "which", "will",
    "with", "you", "your", "for", "how", "why", "who", "via", "than",
    "they", "them", "his", "her", "she", "him", "its", "a", "an", "to",
    "of", "in", "on", "at", "by", "as", "is", "be", "or",
}


def _clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _normalize_title(value):
    text = _clean(value).lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^\w\s\-]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def _tokens(value):
    return {
        token.lower()
        for token in re.findall(
            r"\b[\w\-]{2,}\b",
            _normalize_title(value),
            flags=re.UNICODE,
        )
        if token.lower() not in STOPWORDS
        and not token.isdigit()
    }


def _jaccard(left, right):
    a = _tokens(left)
    b = _tokens(right)

    if not a or not b:
        return 0.0

    union = a | b
    return len(a & b) / len(union) if union else 0.0


def _safe_http_url(url):
    try:
        parsed = urlparse(str(url).strip())
    except Exception:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False

    host = parsed.hostname

    if not host:
        return False

    host_lower = host.lower()

    if host_lower in {"localhost", "127.0.0.1", "::1"}:
        return False

    try:
        ip = ipaddress.ip_address(host_lower)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
        ):
            return False
    except ValueError:
        pass

    return True


def _domain(url):
    try:
        return urlparse(str(url)).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def _language_label_from_text(text, fallback="en"):
    code = detect_script_language(
        text,
        fallback,
    )

    label = NEWS_PROFILES.get(
        code,
        {},
    ).get(
        "label",
        code,
    )

    return code, label


def _score_text(text, fallback="en"):
    code, label = _language_label_from_text(
        text,
        fallback,
    )

    score, method, confidence = score_multilingual_sentiment(
        text,
        code,
    )

    return {
        "Language Code": code,
        "Language": label,
        "Sentiment": float(score),
        "Sentiment Label": sentiment_label(score),
        "Sentiment Method": method,
        "Sentiment Confidence": confidence,
    }


def fetch_gdelt_articles(
    query,
    *,
    timespan="7d",
    max_records=75,
):
    clean_query = _clean(query)

    if not clean_query:
        return pd.DataFrame(), "No query supplied"

    try:
        response = requests.get(
            "https://api.gdeltproject.org/api/v2/doc/doc",
            params={
                "query": clean_query,
                "mode": "artlist",
                "maxrecords": min(
                    max(int(max_records), 1),
                    250,
                ),
                "timespan": timespan,
                "sort": "datedesc",
                "format": "json",
            },
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            },
            timeout=25,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception as error:
        return pd.DataFrame(), str(error)

    articles = payload.get("articles", []) or []
    rows = []

    for item in articles:
        title = _clean(
            item.get("title", "")
        )
        url = _clean(
            item.get("url", "")
        )

        if not title:
            continue

        scored = _score_text(
            title,
            fallback="en",
        )

        rows.append(
            {
                "Headline": title,
                "Source Name": (
                    _clean(
                        item.get("domain", "")
                    )
                    or _domain(url)
                    or "GDELT source"
                ),
                "Source Type": "GDELT",
                "Source Class": "External News",
                "Provider": "GDELT DOC 2.0",
                "Published": _clean(
                    item.get("seendate", "")
                ),
                "Link": url,
                "Source Country": _clean(
                    item.get("sourcecountry", "")
                ),
                "Edition Country": "",
                **scored,
            }
        )

    return pd.DataFrame(rows), ""


def discover_rss_feeds(
    website,
    *,
    max_feeds=5,
):
    website = _clean(website)

    if not website or not _safe_http_url(website):
        return [], "Website URL is unavailable or not safe to request"

    try:
        response = requests.get(
            website,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
            },
            timeout=18,
        )
        response.raise_for_status()
        html = response.text[:500000]
    except Exception as error:
        return [], str(error)

    patterns = [
        r'<link[^>]+type=["\']application/rss\+xml["\'][^>]+href=["\']([^"\']+)["\']',
        r'<link[^>]+href=["\']([^"\']+)["\'][^>]+type=["\']application/rss\+xml["\']',
        r'<link[^>]+type=["\']application/atom\+xml["\'][^>]+href=["\']([^"\']+)["\']',
        r'<link[^>]+href=["\']([^"\']+)["\'][^>]+type=["\']application/atom\+xml["\']',
    ]

    feeds = []

    for pattern in patterns:
        for match in re.findall(
            pattern,
            html,
            flags=re.I,
        ):
            feed_url = urljoin(
                website,
                unescape(match),
            )

            if (
                _safe_http_url(feed_url)
                and feed_url not in feeds
            ):
                feeds.append(feed_url)

            if len(feeds) >= max_feeds:
                break

        if len(feeds) >= max_feeds:
            break

    return feeds, ""


def fetch_rss_articles(
    feed_urls,
    *,
    query="",
    official_domain="",
    limit_per_feed=30,
):
    frames = []
    notes = []

    query_tokens = _tokens(query)

    for feed_url in list(feed_urls or []):
        feed_url = _clean(feed_url)

        if not _safe_http_url(feed_url):
            notes.append(
                f"Skipped unsafe or invalid feed URL: {feed_url}"
            )
            continue

        try:
            response = requests.get(
                feed_url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": (
                        "application/rss+xml,"
                        "application/atom+xml,"
                        "application/xml,"
                        "text/xml,*/*"
                    ),
                },
                timeout=20,
            )
            response.raise_for_status()
            parsed = feedparser.parse(
                response.content
            )
        except Exception as error:
            notes.append(
                f"{feed_url}: {error}"
            )
            continue

        rows = []

        for entry in parsed.entries[
            : max(int(limit_per_feed), 1)
        ]:
            title = _clean(
                getattr(
                    entry,
                    "title",
                    "",
                )
            )

            summary = _clean(
                getattr(
                    entry,
                    "summary",
                    "",
                )
            )

            combined = f"{title} {summary}".strip()

            if not title:
                continue

            if query_tokens:
                item_tokens = _tokens(
                    combined
                )

                if not (
                    query_tokens
                    & item_tokens
                ):
                    continue

            link = _clean(
                getattr(
                    entry,
                    "link",
                    "",
                )
            )

            feed_domain = _domain(
                feed_url
            )

            link_domain = _domain(
                link
            )

            source_name = (
                _clean(
                    getattr(
                        parsed.feed,
                        "title",
                        "",
                    )
                )
                or feed_domain
                or "RSS source"
            )

            source_class = (
                "Primary / Official RSS"
                if official_domain
                and (
                    feed_domain.endswith(
                        official_domain
                    )
                    or link_domain.endswith(
                        official_domain
                    )
                )
                else "Public RSS"
            )

            scored = _score_text(
                title,
                fallback="en",
            )

            rows.append(
                {
                    "Headline": title,
                    "Source Name": source_name,
                    "Source Type": "RSS",
                    "Source Class": source_class,
                    "Provider": feed_url,
                    "Published": _clean(
                        getattr(
                            entry,
                            "published",
                            "",
                        )
                        or getattr(
                            entry,
                            "updated",
                            "",
                        )
                    ),
                    "Link": link,
                    "Source Country": "",
                    "Edition Country": "",
                    **scored,
                }
            )

        if rows:
            frames.append(
                pd.DataFrame(rows)
            )

    if not frames:
        return pd.DataFrame(), notes

    return (
        pd.concat(
            frames,
            ignore_index=True,
        ),
        notes,
    )


def normalize_google_news(
    frame,
):
    if frame is None or frame.empty:
        return pd.DataFrame()

    result = frame.copy()

    result = result.rename(
        columns={
            "Source": "Source Name",
        }
    )

    result["Source Type"] = "Google News"
    result["Source Class"] = "External News"
    result["Provider"] = "Google News RSS"
    result["Source Country"] = ""

    required = [
        "Headline",
        "Source Name",
        "Source Type",
        "Source Class",
        "Provider",
        "Published",
        "Link",
        "Source Country",
        "Edition Country",
        "Language Code",
        "Language",
        "Sentiment",
        "Sentiment Label",
        "Sentiment Method",
        "Sentiment Confidence",
    ]

    for column in required:
        if column not in result.columns:
            result[column] = ""

    return result[required]


def deduplicate_records(
    frame,
):
    if frame is None or frame.empty:
        return pd.DataFrame()

    data = frame.copy()
    data["Canonical Title"] = (
        data["Headline"]
        .map(
            _normalize_title
        )
    )

    data["Canonical URL"] = (
        data["Link"]
        .fillna("")
        .astype(str)
        .str.replace(
            r"[?#].*$",
            "",
            regex=True,
        )
    )

    data = data.drop_duplicates(
        subset=[
            "Canonical URL",
        ],
        keep="first",
    )

    blank_url = (
        data["Canonical URL"]
        .eq("")
    )

    nonblank = data[
        ~blank_url
    ]

    blank = (
        data[
            blank_url
        ]
        .drop_duplicates(
            subset=[
                "Canonical Title",
            ],
            keep="first",
        )
    )

    data = pd.concat(
        [
            nonblank,
            blank,
        ],
        ignore_index=True,
    )

    return data.reset_index(
        drop=True
    )


def cluster_narratives(
    frame,
    *,
    similarity_threshold=0.28,
):
    if frame is None or frame.empty:
        return (
            pd.DataFrame(),
            pd.DataFrame(),
        )

    data = frame.copy().reset_index(
        drop=True
    )

    clusters = []

    for index, row in data.iterrows():
        title = row[
            "Headline"
        ]
        language = row.get(
            "Language",
            "",
        )

        best_cluster = None
        best_score = 0.0

        for cluster in clusters:
            if (
                cluster[
                    "language"
                ]
                and language
                and cluster[
                    "language"
                ] != language
            ):
                continue

            score = _jaccard(
                title,
                cluster[
                    "representative"
                ],
            )

            if score > best_score:
                best_score = score
                best_cluster = cluster

        if (
            best_cluster is not None
            and best_score >= similarity_threshold
        ):
            best_cluster[
                "indices"
            ].append(index)
        else:
            clusters.append(
                {
                    "indices": [index],
                    "representative": title,
                    "language": language,
                }
            )

    assignments = {}

    summary_rows = []

    for cluster_id, cluster in enumerate(
        clusters,
        start=1,
    ):
        subset = data.loc[
            cluster["indices"]
        ].copy()

        source_types = sorted(
            {
                str(value)
                for value in subset[
                    "Source Type"
                ]
                .dropna()
                .tolist()
                if str(value)
            }
        )

        source_classes = sorted(
            {
                str(value)
                for value in subset[
                    "Source Class"
                ]
                .dropna()
                .tolist()
                if str(value)
            }
        )

        publishers = sorted(
            {
                str(value)
                for value in subset[
                    "Source Name"
                ]
                .dropna()
                .tolist()
                if str(value)
            }
        )

        all_tokens = []

        for headline in subset[
            "Headline"
        ].tolist():
            all_tokens.extend(
                list(
                    _tokens(
                        headline
                    )
                )
            )

        top_terms = [
            term
            for term, _
            in Counter(
                all_tokens
            ).most_common(4)
        ]

        label = (
            " • ".join(
                top_terms
            )
            if top_terms
            else cluster[
                "representative"
            ][:90]
        )

        avg_sentiment = float(
            subset[
                "Sentiment"
            ]
            .fillna(0)
            .mean()
        )

        negative_share = float(
            subset[
                "Sentiment"
            ]
            .fillna(0)
            .lt(
                -0.05
            )
            .mean()
            * 100
        )

        source_diversity = len(
            source_types
        )

        publisher_diversity = len(
            publishers
        )

        volume = len(
            subset
        )

        corroboration = (
            "High"
            if source_diversity >= 3
            else "Medium"
            if source_diversity >= 2
            else "Single-source"
        )

        risk = (
            negative_share
            * .55
            + min(
                100.0,
                volume
                * 12.0
            )
            * .20
            + min(
                100.0,
                source_diversity
                / 3
                * 100
            )
            * .15
            + max(
                0.0,
                -avg_sentiment
                * 100
            )
            * .10
        )

        risk = round(
            min(
                100.0,
                max(
                    0.0,
                    risk,
                ),
            ),
            1,
        )

        summary_rows.append(
            {
                "Cluster ID": cluster_id,
                "Narrative Cluster": label,
                "Language": cluster[
                    "language"
                ],
                "Records": volume,
                "Source Types": ", ".join(
                    source_types
                ),
                "Source Classes": ", ".join(
                    source_classes
                ),
                "Source Diversity": source_diversity,
                "Publisher Diversity": publisher_diversity,
                "Cross-Source Confidence": corroboration,
                "Average Sentiment": round(
                    avg_sentiment,
                    3,
                ),
                "Negative Share %": round(
                    negative_share,
                    1,
                ),
                "Narrative Risk": risk,
            }
        )

        for item_index in cluster[
            "indices"
        ]:
            assignments[
                item_index
            ] = cluster_id

    data[
        "Cluster ID"
    ] = [
        assignments[
            index
        ]
        for index in data.index
    ]

    return (
        data,
        pd.DataFrame(
            summary_rows
        )
        .sort_values(
            [
                "Narrative Risk",
                "Records",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .reset_index(
            drop=True
        ),
    )


def retrieval_timestamp():
    return datetime.now(
        timezone.utc
    ).isoformat()
