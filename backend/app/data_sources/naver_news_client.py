"""
네이버뉴스 검색 API 클라이언트 (NAVER API HUB, NCP 방식)
기술1-1(국내) - 당일 경제기사 수집
"""

import os
import re
import html
import requests
from dotenv import load_dotenv

load_dotenv()

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

BASE_URL = "https://naverapihub.apigw.ntruss.com/search/v1/news"


def search_news(query: str, display: int = 20, sort: str = "date") -> list:
    """
    네이버뉴스 검색 (NAVER API HUB)
    query: 검색어 (예: "코스피")
    display: 가져올 기사 수 (최대 100)
    sort: date(최신순) or sim(정확도순)
    """
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        raise ValueError("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET이 설정되지 않았습니다.")

    headers = {
        "X-NCP-APIGW-API-KEY-ID": NAVER_CLIENT_ID,
        "X-NCP-APIGW-API-KEY": NAVER_CLIENT_SECRET,
    }
    params = {
        "query": query,
        "display": display,
        "sort": sort,
    }

    response = requests.get(BASE_URL, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    articles = []
    for item in data.get("items", []):
        # HTML 태그(<b> 등) 및 엔티티(&quot; 등) 제거
        title = html.unescape(re.sub(r"<.*?>", "", item.get("title", "")))
        description = html.unescape(re.sub(r"<.*?>", "", item.get("description", "")))
        articles.append({
            "title": title,
            "description": description,
            "link": item.get("link"),
            "pub_date": item.get("pubDate"),
        })

    return articles


if __name__ == "__main__":
    results = search_news("코스피", display=10)
    print(f"검색 결과: {len(results)}건\n")
    for r in results[:5]:
        print(f"- {r['title']}")
        print(f"  {r['description'][:80]}...")
        print()