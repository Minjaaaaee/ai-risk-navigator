import os
import io
import zipfile
import logging
import time
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

DART_API_KEY = os.getenv("DART_API_KEY")
BASE_URL = "https://opendart.fss.or.kr/api"

class DartClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or DART_API_KEY
        if not self.api_key:
            raise ValueError("DART_API_KEY가 설정되지 않았습니다. backend/.env 파일을 확인하세요.")
        self.session = requests.Session()

    def get_disclosure_list(
        self,
        corp_code: Optional[str] = None,
        bgn_de: Optional[str] = None,
        end_de: Optional[str] = None,
        pblntf_ty: Optional[str] = None,  # 추가 (A: 정기공시, B: 주요사항 등)
        page_count: int = 20,
    ) -> Dict[str, Any]:
        """
        공시 목록 조회
        """
        url = f"{BASE_URL}/list.json"
        params = {
            "crtfc_key": self.api_key,
            "page_count": page_count,
        }
        if corp_code: params["corp_code"] = corp_code
        if bgn_de: params["bgn_de"] = bgn_de
        if end_de: params["end_de"] = end_de
        if pblntf_ty: params["pblntf_ty"] = pblntf_ty  # 파라미터 전달

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "000":
                # '013'은 조회된 데이터가 없는 경우이므로 에러 대신 빈 리스트 반환
                if data.get("status") == "013":
                    logger.info("조회된 공시 데이터가 없습니다.")
                    return {"status": "013", "message": "조회된 데이타가 없습니다.", "list": []}
                
                raise RuntimeError(f"DART API 응답 오류: {data.get('status')} - {data.get('message')}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"DART API HTTP 요청 실패: {e}")
            raise

    def get_document(self, rcept_no: str) -> Optional[str]:
        """
        공시 원문 문서 다운로드 및 XML 추출
        """
        url = f"{BASE_URL}/document.xml"
        params = {
            "crtfc_key": self.api_key,
            "rcept_no": rcept_no,
        }
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()

            if not response.content.startswith(b"PK"):
                try:
                    error_text = response.content.decode("utf-8", errors="ignore")
                except Exception:
                    error_text = str(response.content[:200])
                logger.warning(f"zip이 아닌 응답을 받았습니다. rcept_no={rcept_no}\n응답 내용: {error_text[:300]}")
                return None
            
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                file_names = z.namelist()
                if not file_names:
                    logger.warning(f"공시 원문 zip이 비어있습니다. rcept_no={rcept_no}")
                    return None
                    
                # 여러 파일 중 메인 XML 파일(rcept_no.xml)을 찾거나 확장자가 xml인 첫 번째 파일 선택
                target_file = next((f for f in file_names if f.endswith('.xml')), None)
                if not target_file:
                     logger.warning(f"ZIP 파일 내 XML 문서를 찾을 수 없습니다. rcept_no={rcept_no}")
                     return None

                with z.open(target_file) as f:
                    content = f.read()
                    try:
                        return content.decode("utf-8")
                    except UnicodeDecodeError:
                        return content.decode("euc-kr", errors="ignore")
                        
        except requests.exceptions.RequestException as e:
             logger.error(f"DART 문서 다운로드 실패 (rcept_no={rcept_no}): {e}")
             raise
        except zipfile.BadZipFile:
             logger.error(f"유효하지 않은 ZIP 파일 포맷입니다. rcept_no={rcept_no}")
             return None

if __name__ == "__main__":
    try:
        client = DartClient()
        result = client.get_disclosure_list(page_count=5)
        
        if result.get("list"):
            print(f"조회 성공! 상위 5건:")
            for item in result.get("list"):
                print(f"- [{item['rcept_no']}] {item['corp_name']} : {item['report_nm']} ({item['rcept_dt']})")
                
                # 문서 다운로드 테스트 (API Rate Limit 방지를 위해 딜레이 추가)
                time.sleep(0.5) 
        else:
             print("조회된 공시 목록이 없습니다.")
             
    except Exception as e:
        print(f"테스트 실행 중 오류 발생: {e}")