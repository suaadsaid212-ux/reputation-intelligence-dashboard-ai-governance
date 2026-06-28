import feedparser

from urllib.parse import quote_plus


def get_news(query, limit=20):
    query = str(query).strip()

    if not query or query.lower() == "nan":
        return []

    encoded_query = quote_plus(query)

    url = (
        "https://news.google.com/rss/search"
        f"?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    )

    feed = feedparser.parse(url)

    results = []

    for entry in feed.entries[:limit]:
        results.append({
            "title": entry.title,
            "link": entry.link,
            "published": getattr(entry, "published", ""),
            "source": getattr(
                getattr(entry, "source", None),
                "title",
                "",
            ),
        })

    return results
