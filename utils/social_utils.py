import math
import random
import re
from collections import Counter

import pandas as pd
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


PLATFORM_CATALOG = {
    "YouTube": {
        "source_type": "Video platform",
        "access_mode": "Live with YOUTUBE_API_KEY",
        "data_status": "API key required",
        "geo_scope": "Global platform search; country/user location requires API enrichment",
        "language_scope": "Metadata text; language detection planned",
    },
    "Reddit": {
        "source_type": "Forum/community",
        "access_mode": "Public JSON endpoint; official API recommended",
        "data_status": "Public endpoint attempted",
        "geo_scope": "Subreddit/community level; user geography usually unavailable",
        "language_scope": "Mostly English in public search, but multilingual communities exist",
    },
    "Hacker News": {
        "source_type": "Technology forum",
        "access_mode": "Live public Algolia API",
        "data_status": "Live public API",
        "geo_scope": "Global technology discourse; no reliable user geography",
        "language_scope": "English-dominant",
    },
    "Mastodon / Fediverse": {
        "source_type": "Decentralized social network",
        "access_mode": "Live public instance search",
        "data_status": "Live public API",
        "geo_scope": "Instance-level geography only unless profiles disclose more",
        "language_scope": "Multilingual where status metadata is available",
    },
    "Bluesky": {
        "source_type": "Social network",
        "access_mode": "Connector/API required",
        "data_status": "Connector planned",
        "geo_scope": "Depends on API metadata and ethical collection settings",
        "language_scope": "Multilingual after connector setup",
    },
    "X / Twitter": {
        "source_type": "Social network",
        "access_mode": "Official API required",
        "data_status": "Connector planned",
        "geo_scope": "Depends on API tier, post metadata, and consent/public data rules",
        "language_scope": "Multilingual after connector setup",
    },
    "TikTok": {
        "source_type": "Short-form video platform",
        "access_mode": "Official research/commercial API required",
        "data_status": "Connector planned",
        "geo_scope": "Depends on approved API access and region metadata",
        "language_scope": "Multilingual after connector setup",
    },
    "Instagram": {
        "source_type": "Visual social network",
        "access_mode": "Meta API required",
        "data_status": "Connector planned",
        "geo_scope": "Business/creator/account metadata only where permitted",
        "language_scope": "Multilingual after connector setup",
    },
    "LinkedIn": {
        "source_type": "Professional network",
        "access_mode": "Partner/API access required",
        "data_status": "Connector planned",
        "geo_scope": "Professional and organization metadata where permitted",
        "language_scope": "Multilingual after connector setup",
    },
}


STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "amid",
    "and",
    "are",
    "because",
    "been",
    "being",
    "but",
    "can",
    "could",
    "from",
    "has",
    "have",
    "how",
    "into",
    "its",
    "more",
    "new",
    "not",
    "now",
    "official",
    "our",
    "over",
    "said",
    "says",
    "that",
    "the",
    "their",
    "this",
    "through",
    "using",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "will",
    "with",
    "you",
    "your",
}


def get_social_score(query, youtube_api_key=""):
    rows, _, _ = collect_social_narratives(
        query=query,
        selected_platforms=["YouTube", "Hacker News", "Mastodon / Fediverse"],
        youtube_api_key=youtube_api_key,
        limit_per_platform=15,
    )
    metrics = calculate_social_metrics(rows)

    if metrics["Mentions"] == 0:
        return get_demo_social_score(query)

    return {
        "mentions": metrics["Mentions"],
        "sentiment": round((metrics["SSI"] - 50) / 50, 2),
        "engagement": metrics["Engagement"],
        "source": "multi_platform_social",
    }


def get_demo_social_score(query):
    random.seed(query)

    return {
        "mentions": random.randint(100, 10000),
        "sentiment": round(random.uniform(-1, 1), 2),
        "engagement": random.randint(1000, 100000),
        "source": "demo_fallback",
    }


def get_youtube_score(query, youtube_api_key):
    rows = fetch_youtube_posts(query, youtube_api_key, limit=25)

    if rows.empty:
        return get_demo_social_score(query)

    engagement = int(rows["Engagement"].sum())

    return {
        "mentions": len(rows),
        "sentiment": round(float(rows["Sentiment"].mean()), 2),
        "engagement": engagement,
        "source": "youtube_api",
    }


def collect_social_narratives(
    query,
    selected_platforms,
    youtube_api_key="",
    limit_per_platform=20,
):
    clean_query = str(query or "").strip()
    selected_platforms = list(selected_platforms or [])
    errors = []
    frames = []

    for platform in selected_platforms:
        try:
            if platform == "YouTube":
                frame = fetch_youtube_posts(
                    clean_query,
                    youtube_api_key,
                    limit=limit_per_platform,
                )
            elif platform == "Reddit":
                frame = fetch_reddit_posts(
                    clean_query,
                    limit=limit_per_platform,
                )
            elif platform == "Hacker News":
                frame = fetch_hacker_news_posts(
                    clean_query,
                    limit=limit_per_platform,
                )
            elif platform == "Mastodon / Fediverse":
                frame = fetch_mastodon_posts(
                    clean_query,
                    limit=limit_per_platform,
                )
            else:
                frame = empty_posts_frame()

            if not frame.empty:
                frames.append(frame)

        except Exception as error:
            errors.append(f"{platform}: {error}")

    if frames:
        posts = pd.concat(frames, ignore_index=True)
        posts = posts.drop_duplicates(
            subset=["Platform", "Title", "Url"],
            keep="first",
        )
    else:
        posts = empty_posts_frame()

    coverage = build_platform_coverage(
        selected_platforms,
        posts,
        youtube_api_key=youtube_api_key,
    )

    return posts, coverage, errors


def build_platform_coverage(selected_platforms, posts, youtube_api_key=""):
    rows = []

    for platform in selected_platforms:
        meta = PLATFORM_CATALOG.get(platform, {})
        platform_posts = posts[
            posts["Platform"].eq(platform)
        ] if not posts.empty else pd.DataFrame()

        status = meta.get("data_status", "Unknown")

        if platform == "YouTube" and youtube_api_key:
            status = "Live API connected" if not platform_posts.empty else "API connected; no matching rows"
        elif platform == "YouTube":
            status = "Add YOUTUBE_API_KEY for live data"
        elif platform_posts.empty and status in {"Live public API", "Public endpoint attempted"}:
            status = "No rows returned or endpoint unavailable"
        elif not platform_posts.empty:
            status = "Live rows loaded"

        rows.append({
            "Platform": platform,
            "Source Type": meta.get("source_type", ""),
            "Access Mode": meta.get("access_mode", ""),
            "Data Status": status,
            "Rows": int(len(platform_posts)),
            "Geographic Coverage": meta.get("geo_scope", ""),
            "Language Coverage": meta.get("language_scope", ""),
        })

    return pd.DataFrame(rows)


def fetch_youtube_posts(query, api_key, limit=20):
    if not query or not api_key:
        return empty_posts_frame()

    analyzer = SentimentIntensityAnalyzer()

    search_response = requests.get(
        "https://www.googleapis.com/youtube/v3/search",
        params={
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": min(int(limit), 50),
            "order": "relevance",
            "key": api_key,
        },
        timeout=20,
    )
    search_response.raise_for_status()
    search_data = search_response.json()

    rows = []
    video_ids = []

    for item in search_data.get("items", []):
        video_id = item.get("id", {}).get("videoId")

        if not video_id:
            continue

        snippet = item.get("snippet", {})
        title = clean_text(snippet.get("title", ""))
        description = clean_text(snippet.get("description", ""))
        text = f"{title}. {description}".strip()
        video_ids.append(video_id)

        rows.append({
            "Platform": "YouTube",
            "Source_Type": PLATFORM_CATALOG["YouTube"]["source_type"],
            "Title": title,
            "Text": text,
            "Author": snippet.get("channelTitle", ""),
            "Published_At": snippet.get("publishedAt", ""),
            "Engagement": 0,
            "Sentiment": analyzer.polarity_scores(text or title)["compound"],
            "Sentiment_Label": "",
            "Url": f"https://www.youtube.com/watch?v={video_id}",
            "Data_Status": "Live API",
            "Geo_Scope": PLATFORM_CATALOG["YouTube"]["geo_scope"],
            "Language": "unknown",
        })

    if not rows:
        return empty_posts_frame()

    stats_response = requests.get(
        "https://www.googleapis.com/youtube/v3/videos",
        params={
            "part": "statistics",
            "id": ",".join(video_ids),
            "key": api_key,
        },
        timeout=20,
    )
    stats_response.raise_for_status()
    stats_data = stats_response.json()

    stats_by_id = {}

    for item in stats_data.get("items", []):
        stats = item.get("statistics", {})
        stats_by_id[item.get("id")] = (
            safe_int(stats.get("viewCount"))
            + safe_int(stats.get("likeCount"))
            + safe_int(stats.get("commentCount"))
        )

    for row in rows:
        video_id = row["Url"].split("v=")[-1]
        row["Engagement"] = stats_by_id.get(video_id, 0)
        row["Sentiment_Label"] = sentiment_label(row["Sentiment"])

    return pd.DataFrame(rows)


def fetch_reddit_posts(query, limit=20):
    if not query:
        return empty_posts_frame()

    analyzer = SentimentIntensityAnalyzer()

    response = requests.get(
        "https://www.reddit.com/search.json",
        params={
            "q": query,
            "limit": min(int(limit), 50),
            "sort": "relevance",
            "t": "month",
            "raw_json": 1,
        },
        headers={
            "User-Agent": "ReputationIntelligenceResearchPrototype/0.1",
            "Accept": "application/json",
        },
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()

    rows = []

    for child in payload.get("data", {}).get("children", []):
        item = child.get("data", {})
        title = clean_text(item.get("title", ""))
        text = clean_text(item.get("selftext", ""))
        combined_text = f"{title}. {text}".strip()
        sentiment = analyzer.polarity_scores(combined_text or title)["compound"]
        permalink = item.get("permalink", "")

        rows.append({
            "Platform": "Reddit",
            "Source_Type": PLATFORM_CATALOG["Reddit"]["source_type"],
            "Title": title,
            "Text": combined_text,
            "Author": item.get("subreddit_name_prefixed", ""),
            "Published_At": item.get("created_utc", ""),
            "Engagement": safe_int(item.get("score")) + safe_int(item.get("num_comments")),
            "Sentiment": sentiment,
            "Sentiment_Label": sentiment_label(sentiment),
            "Url": f"https://www.reddit.com{permalink}" if permalink else "",
            "Data_Status": "Live public endpoint",
            "Geo_Scope": PLATFORM_CATALOG["Reddit"]["geo_scope"],
            "Language": "unknown",
        })

    return pd.DataFrame(rows) if rows else empty_posts_frame()


def fetch_hacker_news_posts(query, limit=20):
    if not query:
        return empty_posts_frame()

    analyzer = SentimentIntensityAnalyzer()
    response = requests.get(
        "https://hn.algolia.com/api/v1/search",
        params={
            "query": query,
            "tags": "story",
            "hitsPerPage": min(int(limit), 50),
        },
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()

    rows = []

    for item in payload.get("hits", []):
        title = clean_text(item.get("title") or item.get("story_title") or "")
        if not title:
            continue

        sentiment = analyzer.polarity_scores(title)["compound"]
        url = item.get("url") or f"https://news.ycombinator.com/item?id={item.get('objectID')}"

        rows.append({
            "Platform": "Hacker News",
            "Source_Type": PLATFORM_CATALOG["Hacker News"]["source_type"],
            "Title": title,
            "Text": title,
            "Author": item.get("author", ""),
            "Published_At": item.get("created_at", ""),
            "Engagement": safe_int(item.get("points")) + safe_int(item.get("num_comments")),
            "Sentiment": sentiment,
            "Sentiment_Label": sentiment_label(sentiment),
            "Url": url,
            "Data_Status": "Live public API",
            "Geo_Scope": PLATFORM_CATALOG["Hacker News"]["geo_scope"],
            "Language": "en",
        })

    return pd.DataFrame(rows) if rows else empty_posts_frame()


def fetch_mastodon_posts(query, limit=20, instance="mastodon.social"):
    if not query:
        return empty_posts_frame()

    analyzer = SentimentIntensityAnalyzer()
    response = requests.get(
        f"https://{instance}/api/v2/search",
        params={
            "q": query,
            "type": "statuses",
            "limit": min(int(limit), 40),
            "resolve": "false",
        },
        headers={
            "Accept": "application/json",
        },
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()

    rows = []

    for item in payload.get("statuses", []):
        text = clean_text(strip_html(item.get("content", "")))
        if not text:
            continue

        account = item.get("account", {}) or {}
        sentiment = analyzer.polarity_scores(text)["compound"]

        rows.append({
            "Platform": "Mastodon / Fediverse",
            "Source_Type": PLATFORM_CATALOG["Mastodon / Fediverse"]["source_type"],
            "Title": shorten_text(text, limit=120),
            "Text": text,
            "Author": account.get("acct", ""),
            "Published_At": item.get("created_at", ""),
            "Engagement": (
                safe_int(item.get("reblogs_count"))
                + safe_int(item.get("favourites_count"))
                + safe_int(item.get("replies_count"))
            ),
            "Sentiment": sentiment,
            "Sentiment_Label": sentiment_label(sentiment),
            "Url": item.get("url", ""),
            "Data_Status": f"Live public API: {instance}",
            "Geo_Scope": f"Public instance: {instance}",
            "Language": item.get("language") or "unknown",
        })

    return pd.DataFrame(rows) if rows else empty_posts_frame()


def calculate_social_metrics(posts):
    if posts.empty:
        return {
            "SSI": 50.0,
            "SVI": 0.0,
            "NPI": 0.0,
            "SRS": 0.0,
            "SES": 0.0,
            "Mentions": 0,
            "Engagement": 0,
            "Platforms": 0,
            "Risk_Label": "No live social rows",
        }

    mentions = int(len(posts))
    engagement = int(posts["Engagement"].fillna(0).sum())
    platform_count = int(posts["Platform"].nunique())
    mean_sentiment = float(posts["Sentiment"].fillna(0).mean())
    negative_ratio = float(posts["Sentiment"].lt(-0.05).mean() * 100)

    ssi = round((mean_sentiment + 1) * 50, 2)
    svi = round(min(100, mentions * 4), 2)
    ses = round(min(100, math.log1p(max(engagement, 0)) / math.log1p(100000) * 100), 2)
    platform_spread = min(100, platform_count * 20)
    npi = round(min(100, negative_ratio * 0.65 + svi * 0.25 + platform_spread * 0.10), 2)
    srs = round(0.40 * npi + 0.30 * (100 - ssi) + 0.20 * svi + 0.10 * ses, 2)

    return {
        "SSI": ssi,
        "SVI": svi,
        "NPI": npi,
        "SRS": srs,
        "SES": ses,
        "Mentions": mentions,
        "Engagement": engagement,
        "Platforms": platform_count,
        "Risk_Label": social_risk_label(srs),
    }


def summarize_platforms(posts):
    if posts.empty:
        return pd.DataFrame(
            columns=[
                "Platform",
                "Mentions",
                "Engagement",
                "Average Sentiment",
                "Negative Share",
                "Languages",
            ]
        )

    grouped = posts.groupby("Platform", dropna=False)
    summary = grouped.agg(
        Mentions=("Title", "count"),
        Engagement=("Engagement", "sum"),
        Sentiment=("Sentiment", "mean"),
        Languages=("Language", lambda values: ", ".join(sorted(set(str(v) for v in values if str(v)))))
    ).reset_index()

    negative_share = grouped["Sentiment"].apply(lambda values: round(float(values.lt(-0.05).mean() * 100), 2))
    summary["Negative Share"] = summary["Platform"].map(negative_share)
    summary["Average Sentiment"] = summary["Sentiment"].round(3)
    summary = summary.drop(columns=["Sentiment"])

    return summary.sort_values(["Mentions", "Engagement"], ascending=False)


def extract_terms(posts, top_n=12):
    if posts.empty:
        return pd.DataFrame(columns=["Term", "Frequency"])

    text = " ".join(posts["Text"].fillna("").astype(str).tolist()).lower()
    tokens = re.findall(r"[a-z][a-z0-9\-]{2,}", text)
    counts = Counter(
        token for token in tokens
        if token not in STOPWORDS and not token.startswith("http")
    )

    return pd.DataFrame(
        counts.most_common(top_n),
        columns=["Term", "Frequency"],
    )


def empty_posts_frame():
    return pd.DataFrame(
        columns=[
            "Platform",
            "Source_Type",
            "Title",
            "Text",
            "Author",
            "Published_At",
            "Engagement",
            "Sentiment",
            "Sentiment_Label",
            "Url",
            "Data_Status",
            "Geo_Scope",
            "Language",
        ]
    )


def sentiment_label(value):
    value = float(value or 0)

    if value >= 0.05:
        return "Positive"
    if value <= -0.05:
        return "Negative"
    return "Neutral"


def social_risk_label(score):
    if score <= 20:
        return "Stable"
    if score <= 40:
        return "Monitor"
    if score <= 60:
        return "Elevated"
    if score <= 80:
        return "High Risk"
    return "Critical"


def clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def strip_html(value):
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    return text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")


def shorten_text(value, limit=120):
    text = clean_text(value)

    if len(text) <= limit:
        return text

    return f"{text[:limit - 3]}..."


def safe_int(value):
    try:
        return int(value or 0)
    except Exception:
        return 0
