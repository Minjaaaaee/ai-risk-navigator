"""
기술3 - 약관/공시 RAG 검색 모듈
저장된 청크 중 질문(쿼리)과 유사한 청크를 찾아오는 검색 기능
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.services.rag.ingest import get_embedding_model
from app.db.vectordb import search_similar_chunks


def search(query: str, match_count: int = 5, filter_rcept_no: str = None):
    """
    자연어 질문을 임베딩으로 변환 후 유사 청크 검색
    """
    model = get_embedding_model()
    query_embedding = model.encode(query).tolist()

    results = search_similar_chunks(
        query_embedding=query_embedding,
        match_count=match_count,
        filter_rcept_no=filter_rcept_no,
    )
    return results

if __name__ == "__main__":
    # 이슈 #3 완료 기준 테스트:
    # 저장된 공시 대상으로 특정 키워드 검색 시 관련성 높은 청크가 조회되는지 확인
    test_queries = ["위험등급", "회사명", "대표이사"]

    for q in test_queries:
        print(f"\n{'=' * 60}")
        print(f"검색어: '{q}'")
        print("=" * 60)

        results = search(q, match_count=3)

        if not results:
            print("검색 결과가 없습니다.")
            continue

        for r in results:
            print(f"\n[유사도: {r['similarity']:.4f}] {r['corp_name']} (청크 #{r['chunk_index']})")
            print(f"내용: {r['content'][:150]}...")