"""
tech 3 - 약관/공시 "쉬운 말 번역" AI
PDF/HTML/XML 원문에서 순수 텍스트를 정제/추출하는 전처리 모듈
"""

import os
import re
import sys
from typing import Optional
from bs4 import BeautifulSoup


def extract_text_from_dart_xml(xml_content: Optional[str]) -> str:
    """
    DART 공시 원문(XML)에서 태그를 제거하고 문단/항목 구조를 보존하여 텍스트 추출
    """
    if not xml_content:
        return ""

    # DART 비표준 XML 태그 대응을 위해 html.parser 활용
    soup = BeautifulSoup(xml_content, "html.parser")

    # 문서 메타정보나 스타일 태그 제거
    for tag in soup(["script", "style", "meta"]):
        tag.decompose()

    # 줄바꿈 구분자로 텍스트 추출 (표와 조항 구조 보존)
    text = soup.get_text(separator="\n")

    # 줄 단위 공백 정리 및 과도한 빈 줄 압축
    lines = [line.strip() for line in text.splitlines()]
    cleaned_lines = [line for line in lines if line]
    cleaned_text = "\n".join(cleaned_lines)

    return cleaned_text

if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    from app.data_sources.dart_client import DartClient

    client = DartClient()
    # 정기공시(A: 사업/분기/반기보고서) 기준으로 조회
    result = client.get_disclosure_list(page_count=5, pblntf_ty="A")

    if not result.get("list"):
        print("조회된 공시가 없습니다.")
        sys.exit(0)

    for item in result["list"]:
        rcept_no = item["rcept_no"]
        print(f"\n시도: {item['corp_name']} - {item['report_nm']} (rcept_no={rcept_no})")

        xml_raw = client.get_document(rcept_no)
        if xml_raw is None:
            print("  -> 문서 없음 (014 등), 다음 공시로 넘어갑니다.")
            continue

        text = extract_text_from_dart_xml(xml_raw)
        if text:
            print("=" * 50)
            print(f"추출 성공! 텍스트 길이: {len(text)}자")
            print("=" * 50)
            print("텍스트 미리보기 (앞 400자):\n")
            print(text[:400])
            break