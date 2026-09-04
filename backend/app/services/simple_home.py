"""
기술2-4 - 심플홈 통합
우선순위 규칙에 따라 카드를 정렬하고, 리밸런싱 카드에는 LLM 설명을 붙여 반환
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app.services.optimizer import optimize_portfolio
from app.services.llm_explain import explain_rebalancing_card

REBALANCE_THRESHOLD_PP = 10.0  # 리밸런싱 괴리도 임계치 (%p)

# MVP 단순화: 교육콘텐츠는 정적 하드코딩 (추후 콘텐츠팀 연동)
EDUCATION_CARD = {
    "priority": 5,
    "type": "education",
    "title": "오늘의 투자 상식",
    "content": "분산투자는 왜 중요할까요? 서로 다른 자산군은 시장 상황에 따라 반대로 움직이는 경우가 많아, 함께 담으면 전체 변동성을 낮출 수 있어요.",
}


def build_rebalancing_card(risk_profile: str, current_allocation: dict, user_profile: str = "위험중립형") -> dict:
    """
    우선순위 2 - 리밸런싱 괴리도 카드 생성 (괴리도가 임계치 미만이면 None 반환)
    """
    result = optimize_portfolio(risk_profile=risk_profile, current_allocation=current_allocation)

    max_diff = max(abs(v) for v in result["allocation_diff"].values())

    if max_diff < REBALANCE_THRESHOLD_PP:
        return None

    explanation = explain_rebalancing_card(result, user_profile=user_profile)

    return {
        "priority": 2,
        "type": "rebalancing",
        "title": "포트폴리오 리밸런싱 제안",
        "max_diff_pp": round(max_diff, 1),
        "detail": result,
        "explanation": explanation,
    }


def build_simple_home(risk_profile: str = "위험중립형", current_allocation: dict = None, user_profile: str = "위험중립형") -> dict:
    """
    카드들을 우선순위 순으로 정렬해 심플홈 응답 생성
    MVP 범위: 우선순위 2(리밸런싱) + 5(교육콘텐츠, 폴백)만 실제 연동
    나머지(1, 3, 4)는 기존 서비스(기술1, 기술2-1, DART) 연동 자리로 TODO 표시
    """
    cards = []

    # TODO: 우선순위 1 - 보유종목 급변이벤트 카드 (기술1-2/1-4 연동)
    # TODO: 우선순위 3 - 해외국면 급변 카드 (기술2-1 연동)
    # TODO: 우선순위 4 - 신규공시 카드 (DART 연동)

    if current_allocation:
        rebalancing_card = build_rebalancing_card(risk_profile, current_allocation, user_profile)
        if rebalancing_card:
            cards.append(rebalancing_card)

    if not cards:
        cards.append(EDUCATION_CARD)

    cards.sort(key=lambda c: c["priority"])

    return {"cards": cards}


if __name__ == "__main__":
    sample_current = {"국내주식": 50, "해외주식": 20, "채권": 20, "현금": 10}

    home = build_simple_home(
        risk_profile="위험중립형",
        current_allocation=sample_current,
        user_profile="위험중립형",
    )

    print("=" * 60)
    print(f"심플홈 카드 개수: {len(home['cards'])}")
    print("=" * 60)
    for card in home["cards"]:
        print(f"\n[우선순위 {card['priority']}] {card['title']}")
        if card["type"] == "rebalancing":
            print(f"괴리도: {card['max_diff_pp']}%p")
            print(f"설명: {card['explanation']}")
        else:
            print(card.get("content", ""))