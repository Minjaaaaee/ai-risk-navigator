"""
기술3 - 규칙기반 위험등급 매칭 로직
상품 위험등급(1~6) vs 사용자 리스크허용도(1~6)를 비교해 적합/주의/부적합 판정.
판정 자체는 LLM에 맡기지 않고 규칙으로 고정 -> 설명가능성 확보.
LLM은 이 판정 결과와 근거청크를 받아 "왜 그런지"만 자연어로 설명.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.services.rag.retrieve import search
from app.services.llm_explain import _call_llm


def match_risk(product_grade: int, user_tolerance: int) -> dict:
    """
    규칙기반 판정
    product_grade: 상품 위험등급 (1=매우낮음 ~ 6=매우높음, 공시상 표기 기준)
    user_tolerance: 사용자가 감내 가능한 위험등급 (1~6)
    """
    if not (1 <= product_grade <= 6) or not (1 <= user_tolerance <= 6):
        raise ValueError("등급은 1~6 사이여야 합니다.")

    diff = product_grade - user_tolerance

    if diff <= 0:
        label = "적합"
    elif diff == 1:
        label = "주의"
    else:
        label = "부적합"

    return {
        "product_grade": product_grade,
        "user_tolerance": user_tolerance,
        "diff": diff,
        "label": label,
    }


def explain_risk_match(
    product_grade: int,
    user_tolerance: int,
    corp_name: str = None,
    rcept_no: str = None,
) -> dict:
    """
    판정 결과 + 관련 근거청크를 조합해 자연어 설명 생성
    """
    match_result = match_risk(product_grade, user_tolerance)

    # 위험/수수료 관련 근거청크 검색 (RAG 재사용)
    queries = ["위험등급", "수수료", "해지 조건"]
    all_chunks = []
    for q in queries:
        chunks = search(q, match_count=2, filter_rcept_no=rcept_no)
        all_chunks.extend(chunks)

    context = "\n\n---\n\n".join(
        f"[근거] {c['content'][:200]}" for c in all_chunks[:5]
    )

    prompt = f"""당신은 금융상품을 일반 투자자에게 쉽게 설명하는 도우미입니다.

상품 위험등급: {product_grade}등급 (1=매우낮음 ~ 6=매우높음)
사용자 리스크허용도: {user_tolerance}등급
판정 결과: {match_result['label']}

아래는 관련 공시 근거자료입니다:
{context}

위 정보를 바탕으로, 이 판정이 나온 이유를 전문용어 없이 쉬운 말로 2~3문장으로 설명하세요.
판정 라벨 자체를 바꾸지 말고, 왜 이 판정이 나왔는지만 설명하세요."""

    explanation = _call_llm(prompt)

    return {
        **match_result,
        "explanation": explanation,
    }


if __name__ == "__main__":
    # 이슈 #5 완료 기준 테스트:
    # 임의의 상품등급/사용자등급 조합에 대해 판정 라벨 + 설명이 정상 생성되는지 확인
    test_cases = [
        {"product_grade": 4, "user_tolerance": 2},  # 부적합 예상
        {"product_grade": 3, "user_tolerance": 2},  # 주의 예상
        {"product_grade": 2, "user_tolerance": 4},  # 적합 예상
    ]

    for case in test_cases:
        print(f"\n{'=' * 60}")
        print(f"상품등급: {case['product_grade']} / 사용자허용도: {case['user_tolerance']}")
        print("=" * 60)

        result = explain_risk_match(
            product_grade=case["product_grade"],
            user_tolerance=case["user_tolerance"],
        )

        print(f"판정: {result['label']} (등급차: {result['diff']})")
        print(f"설명: {result['explanation']}")