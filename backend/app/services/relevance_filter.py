"""
기술1-1 - 관련성 필터링
종목명/지수 키워드와 뉴스 제목/본문 간 임베딩 코사인 유사도로 관련 뉴스만 선별
"""

import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

_embedding_model = None


def get_embedding_model():
    """
    ingest.py와 동일한 모델 재사용 (관련성필터, RAG검색 공통 사용)
    """
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer("jhgan/ko-sroberta-multitask")
    return _embedding_model


def filter_relevant_news(keyword: str, articles: list, threshold: float = 0.3) -> list:
    """
    키워드와 유사도가 threshold 이상인 뉴스만 필터링
    articles: [{title, description, link, pub_date}, ...]
    """
    if not articles:
        return []

    model = get_embedding_model()

    keyword_embedding = model.encode(keyword)

    texts = [f"{a['title']} {a['description']}" for a in articles]
    article_embeddings = model.encode(texts)

    import numpy as np

    def cosine_sim(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    filtered = []
    for article, emb in zip(articles, article_embeddings):
        sim = cosine_sim(keyword_embedding, emb)
        if sim >= threshold:
            filtered.append({**article, "relevance_score": round(float(sim), 4)})

    filtered.sort(key=lambda x: x["relevance_score"], reverse=True)
    return filtered


if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "app", "data_sources"))
    from app.data_sources.naver_news_client import search_news

    keyword = "코스피"
    articles = search_news(keyword, display=20)
    print(f"전체 뉴스: {len(articles)}건")

    filtered = filter_relevant_news(keyword, articles, threshold=0.3)
    print(f"관련성 필터링 후: {len(filtered)}건\n")

    for a in filtered[:5]:
        print(f"[{a['relevance_score']}] {a['title']}")