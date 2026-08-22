"""
기술3 - 검색된 청크를 근거로 쉬운 말 요약 생성
LLM: Gemini 2.5 Flash (무료 티어) — 추후 Claude 등으로 교체 가능하도록 _call_llm 함수만 분리
"""

import os
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


def _build_prompt(question: str, chunks: list) -> str:
    """
    모델에 무관하게 재사용되는 프롬프트 구성 로직
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


def _call_llm(prompt: str) -> str:
    """
    실제 LLM 호출부. 지금은 Gemini 3.6 Flash(무료).
    나중에 Claude API로 바꿀 때는 이 함수 내부만 교체하면 됨.
    """
    client = get_gemini_client()
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )
    return response.text


def summarize_chunks(question: str, chunks: list) -> str:
    """
    검색된 청크들을 근거자료로 삼아 사용자 질문에 쉬운 말로 답변 생성
    chunks: retrieve.py의 search() 결과 리스트
    """
    prompt = _build_prompt(question, chunks)
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