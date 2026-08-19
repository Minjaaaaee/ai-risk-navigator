"""
기술3 - 약관/공시 "쉬운 말 번역" AI
공시 원문 전처리, 청킹(Chunking), 임베딩(Embedding), 벡터DB 적재 파이프라인
"""

import os
import sys
import warnings
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from sentence_transformers import SentenceTransformer

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# 싱글톤 패턴으로 임베딩 모델 캐싱 (중복 로딩 방지)
_EMBEDDING_MODEL = None
EMBEDDING_MODEL_NAME = "jhgan/ko-sroberta-multitask"


def get_embedding_model() -> SentenceTransformer:
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        print(f"임베딩 모델 로드 중: {EMBEDDING_MODEL_NAME}...")
        _EMBEDDING_MODEL = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _EMBEDDING_MODEL


def extract_text_from_dart_xml(xml_content: Optional[str]) -> str:
    """DART 공시 XML에서 텍스트 정제 추출"""
    if not xml_content:
        return ""

    soup = BeautifulSoup(xml_content, "html.parser")
    for tag in soup(["script", "style", "meta"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join([line for line in lines if line])


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    문맥 유실 방지를 위한 슬라이딩 윈도우 기반 텍스트 청킹
    """
    if not text:
        return []

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += (chunk_size - overlap)

    return chunks


def process_and_store_disclosure(
    rcept_no: str,
    corp_name: str,
    report_nm: str,
    raw_xml: str,
    max_test_chunks: int = 10  # 빠른 테스트를 위해 상위 청크 수 제한 (실제 운영 시 None)
) -> int:
    """
    공시 1건을 전처리 -> 청킹 -> 임베딩 -> Supabase 적재하는 통합 파이프라인
    """
    from app.db.vectordb import insert_chunks

    # 1. 텍스트 추출
    text = extract_text_from_dart_xml(raw_xml)
    if not text:
        print("추출된 텍스트가 없습니다.")
        return 0

    # 2. 청킹
    raw_chunks = chunk_text(text, chunk_size=500, overlap=50)
    if max_test_chunks:
        raw_chunks = raw_chunks[:max_test_chunks]

    print(f"생성된 청크 수 (테스트 제한 적용): {len(raw_chunks)}개")

    # 3. 임베딩 생성
    model = get_embedding_model()
    embeddings = model.encode(raw_chunks, show_progress_bar=True, convert_to_numpy=True)

    # 4. DB 적재용 데이터 구성
    payload = []
    for idx, (chunk, emb) in enumerate(zip(raw_chunks, embeddings)):
        payload.append({
            "rcept_no": rcept_no,
            "corp_name": corp_name,
            "report_nm": report_nm,
            "chunk_index": idx,
            "content": chunk,
            "embedding": emb.tolist(),
        })

    # 5. Supabase 적재
    insert_chunks(payload)
    return len(payload)


if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    from app.data_sources.dart_client import DartClient
    from app.db.vectordb import fetch_chunks_by_rcept_no

    client = DartClient()
    print("정기공시 목록 조회 중...")
    result = client.get_disclosure_list(page_count=5, pblntf_ty="A")

    if not result.get("list"):
        print("공시 목록이 없습니다.")
        sys.exit(0)

    # 첫 번째 유효 공시 1건 처리
    for item in result["list"]:
        rcept_no = item["rcept_no"]
        corp_name = item["corp_name"]
        report_nm = item["report_nm"]

        xml_raw = client.get_document(rcept_no)
        if xml_raw is None:
            continue

        print(f"\n[파이프라인 실행] {corp_name} - {report_nm} (rcept_no: {rcept_no})")
        saved_count = process_and_store_disclosure(
            rcept_no=rcept_no,
            corp_name=corp_name,
            report_nm=report_nm,
            raw_xml=xml_raw,
            max_test_chunks=10  # 최초 테스트는 10개만 적재
        )

        if saved_count > 0:
            print("\n[DB 적재 검증] Supabase에서 청크 다시 조회...")
            fetched = fetch_chunks_by_rcept_no(rcept_no)
            print(f"조회된 청크 수: {len(fetched)}개")
            if fetched:
                print(f"첫 번째 청크 내용 미리보기:\n{fetched[0]['content'][:200]}...")
            break