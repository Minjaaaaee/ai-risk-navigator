"""
LLM 설명 레이어 (공통)
기술3 - 공시 쉬운말 요약 (summarize_chunks)
기술2-4 - 리밸런싱/코멘터리 자연어 설명 (explain_rebalancing_card, explain_index_commentary_card)
LLM: Gemini 2.5 Flash (무료 티어) — 추후 Claude 등으로 교체 가능하도록 _call_llm 함수만 분리
"""

import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

_client = None


def get_gemini_client():
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. backend/.env를 확인하세요.")
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def _call_llm(prompt: str, max_retries: int = 3) -> str:
    """
    실제 LLM 호출부 (공통). 지금은 Gemini(무료 티어).
    나중에 Claude API로 바꿀 때는 이 함수 내부만 교체하면 전체(기술3+기술2-4)에 동일 적용됨.
    무료 티어는 분당 요청수 제한(429)이 있어 재시도 로직 포함.
    """
    client = get_gemini_client()

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
            )
            return response.text
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                wait_time = 65  # 분당 한도이므로 넉넉하게 65초 대기
            else:
                wait_time = 2 ** attempt

            if attempt < max_retries - 1:
                print(f"  -> API 호출 실패, {wait_time}초 후 재시도 ({attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                raise


# ============================================================
# 기술3 - 공시 쉬운말 요약
# ============================================================

def _build_rag_prompt(question: str, chunks: list) -> str:
    """
    RAG 검색 결과(chunks)를 근거로 답변 프롬프트 구성
    """
    context = "\n\n---\n\n".join(
        f"[근거 {i+1}] (유사도 {c['similarity']:.2f})\n{c['content']}"
        for i, c in enumerate(chunks)
    )

    return f"""당신은 금융 공시 문서를 일반 투자자에게 쉽게 설명하는 도우미입니다.

아래는 공시 문서에서 검색된 관련 근거자료입니다:

{context}

사용자 질문: {question}

위 근거자료만 사용해서, 전문용어 없이 쉬운 말로 답변해주세요.
근거자료에 답이 없으면 "제공된 자료에서 확인할 수 없습니다"라고 답하세요.
답변은 3~5문장 이내로 간결하게 작성하세요."""


def summarize_chunks(question: str, chunks: list) -> str:
    """
    검색된 청크들을 근거자료로 삼아 사용자 질문에 쉬운 말로 답변 생성
    chunks: retrieve.py의 search() 결과 리스트
    """
    prompt = _build_rag_prompt(question, chunks)
    return _call_llm(prompt)


# ============================================================
# 기술2-4 - 심플홈 카드 자연어 설명
# ============================================================

TONE_BY_PROFILE = {
    "안정형": "차분하고 신중한 톤으로, 리스크 관리를 강조해서",
    "안정추구형": "안정성을 우선하되 기회도 놓치지 않도록 균형있게",
    "위험중립형": "객관적이고 담백한 톤으로",
    "적극투자형": "기회 요인을 적극적으로 짚어주는 톤으로",
    "공격투자형": "간결하고 임팩트 있게, 핵심만",
}


def _build_rebalancing_prompt(optimizer_result: dict, tone: str) -> str:
    diff = optimizer_result.get("allocation_diff", {})
    current = optimizer_result.get("current_allocation", {})
    recommended = optimizer_result.get("recommended_allocation", {})

    diff_text = ", ".join(
        f"{asset} {current.get(asset, 0)}%→{recommended.get(asset, 0)}%"
        for asset in recommended
    )

    return f"""당신은 금융 서비스의 AI 설명 어시스턴트입니다.
아래 포트폴리오 리밸런싱 결과를 사용자에게 설명해주세요.

배분 변화: {diff_text}
리스크프로필: {optimizer_result.get('risk_profile')}

요구사항:
- {tone} 설명할 것
- Sharpe ratio, 공분산, Black-Litterman 같은 전문용어는 절대 쓰지 말 것
- "지금 이런 이유로 OO 비중을 늘리는 게 좋습니다" 형태로 결론부터 말할 것
- 3문장 이내로 간결하게
"""


def explain_rebalancing_card(optimizer_result: dict, user_profile: str = "위험중립형") -> str:
    """
    포트폴리오 최적화 결과(optimizer.py 출력)를 받아 자연어 설명 생성
    """
    tone = TONE_BY_PROFILE.get(user_profile, TONE_BY_PROFILE["위험중립형"])
    prompt = _build_rebalancing_prompt(optimizer_result, tone)
    return _call_llm(prompt)


def explain_index_commentary_card(commentary_text: str, user_profile: str = "위험중립형") -> str:
    """
    기술1 코멘터리 텍스트를 사용자 프로필 톤으로 재구성 (선택적으로 사용)
    """
    tone = TONE_BY_PROFILE.get(user_profile, TONE_BY_PROFILE["위험중립형"])

    prompt = f"""아래 시장 코멘터리를 {tone} 2문장으로 요약해주세요.
전문용어는 쉬운 말로 풀어써주세요.

원문: {commentary_text}
"""

    return _call_llm(prompt)


if __name__ == "__main__":
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
    from app.services.rag.retrieve import search

    question = "이 회사는 어떤 사업을 하나요?"
    print(f"질문: {question}\n")

    chunks = search(question, match_count=3)
    if not chunks:
        print("검색된 근거자료가 없습니다.")
        sys.exit(0)

    print("검색된 근거 청크 수:", len(chunks))
    print("\n답변 생성 중...\n")

    answer = summarize_chunks(question, chunks)
    print("=" * 60)
    print("답변:")
    print("=" * 60)
    print(answer)