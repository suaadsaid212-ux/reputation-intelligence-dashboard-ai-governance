import pandas as pd

from pytrends.request import TrendReq


def get_trends(
    keyword,
    timeframe="today 12-m",
    geo="",
):
    keyword = str(keyword).strip()

    if not keyword or keyword.lower() == "nan":
        return pd.DataFrame()

    try:
        pytrends = TrendReq(
            hl="en-US",
            tz=360,
            timeout=(10, 25),
        )

        pytrends.build_payload(
            [keyword],
            cat=0,
            timeframe=timeframe,
            geo=geo,
            gprop="",
        )

        data = pytrends.interest_over_time()

        if "isPartial" in data.columns:
            data = data.drop(columns=["isPartial"])

        return data

    except Exception:
        return pd.DataFrame()
