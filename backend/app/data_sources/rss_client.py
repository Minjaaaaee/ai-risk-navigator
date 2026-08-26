"""
해외 뉴스 수집 클라이언트 (yfinance 뉴스 기능 활용)
기술1-1(해외) - Reuters RSS가 공개 제공 중단되어 Yahoo Finance 뉴스로 대체
"""

import yfinance as yf

INDEX_TICKERS = {
    "나스닥": "^IXIC",
    "S&P500": "^GSPC",
}


def fetch_rss_articles(feed_key: str = "나스닥", max_items: int = 20) -> list:
    """
    Yahoo Finance에서 해당 지수 관련 최신 뉴스 수집
    feed_key: "나스닥" or "S&P500" (지수명으로 관련뉴스 조회)
    """
    ticker_symbol = INDEX_TICKERS.get(feed_key, "^IXIC")
    ticker = yf.Ticker(ticker_symbol)

    raw_news = ticker.news or []

    articles = []
    for item in raw_news[:max_items]:
        content = item.get("content", item)  # yfinance 버전에 따라 구조가 다를 수 있어 방어적으로 처리
        title = content.get("title", "")
        summary = content.get("summary", "") or content.get("description", "")
        link = content.get("canonicalUrl", {}).get("url", "") if isinstance(content.get("canonicalUrl"), dict) else content.get("link", "")
        pub_date = content.get("pubDate", "")

        articles.append({
            "title": title,
            "description": summary,
            "link": link,
            "pub_date": pub_date,
        })

    return articles


if __name__ == "__main__":
    articles = fetch_rss_articles("나스닥", max_items=10)
    print(f"수집된 기사: {len(articles)}건\n")
    for a in articles[:5]:
        print(f"- {a['title']}")
        print(f"  {a['description'][:80]}...")