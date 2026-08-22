"""
KIS(한국투자증권) Open API 클라이언트
기술1-1(국내) - 코스피/코스닥 지수 및 종목 시세 조회
"""

import os
import time
import json
import requests
from dotenv import load_dotenv

load_dotenv()

KIS_APP_KEY = os.getenv("KIS_APP_KEY")
KIS_APP_SECRET = os.getenv("KIS_APP_SECRET")
KIS_ACCOUNT_NO = os.getenv("KIS_ACCOUNT_NO")
KIS_ACCOUNT_PRODUCT_CD = os.getenv("KIS_ACCOUNT_PRODUCT_CD")

BASE_URL = "https://openapi.koreainvestment.com:9443"

INDEX_CODES = {
    "코스피": "0001",
    "코스닥": "1001",
}


class KISClient:
    def __init__(self):
        if not KIS_APP_KEY or not KIS_APP_SECRET:
            raise ValueError("KIS_APP_KEY / KIS_APP_SECRET이 설정되지 않았습니다. backend/.env를 확인하세요.")
        self._access_token = None
        self._token_expires_at = 0

    def _get_access_token(self) -> str:
        """
        OAuth 접근 토큰 발급 (유효기간 24시간)
        파일에 캐싱해서 프로세스가 재시작돼도 재사용 (1일 1회 발급 원칙 준수)
        """
        token_cache_path = os.path.join(os.path.dirname(__file__), ".kis_token_cache.json")

        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

        if os.path.exists(token_cache_path):
            with open(token_cache_path, "r") as f:
                cached = json.load(f)
            if time.time() < cached.get("expires_at", 0):
                self._access_token = cached["access_token"]
                self._token_expires_at = cached["expires_at"]
                return self._access_token

        url = f"{BASE_URL}/oauth2/tokenP"
        body = {
            "grant_type": "client_credentials",
            "appkey": KIS_APP_KEY,
            "appsecret": KIS_APP_SECRET,
        }
        response = requests.post(url, json=body, timeout=10)
        response.raise_for_status()
        data = response.json()

        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + int(data.get("expires_in", 86400)) - 60

        with open(token_cache_path, "w") as f:
            json.dump({
                "access_token": self._access_token,
                "expires_at": self._token_expires_at,
            }, f)

        return self._access_token

    def _headers(self, tr_id: str) -> dict:
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self._get_access_token()}",
            "appkey": KIS_APP_KEY,
            "appsecret": KIS_APP_SECRET,
            "tr_id": tr_id,
        }

    def get_index_price(self, index_name: str = "코스피") -> dict:
        """
        업종(지수) 현재가 시세 조회
        """
        code = INDEX_CODES.get(index_name)
        if not code:
            raise ValueError(f"알 수 없는 지수명: {index_name}")

        url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-index-price"
        headers = self._headers(tr_id="FHPUP02100000")
        params = {
            "FID_COND_MRKT_DIV_CODE": "U",
            "FID_INPUT_ISCD": code,
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code != 200:
            print(f"[에러 응답 - {index_name}] status={response.status_code}")
            print(f"[에러 본문] {response.text}")

        response.raise_for_status()
        return response.json()

    def get_index_daily_chart(self, index_name: str = "코스피", period_days: int = 30) -> dict:
        """
        지수 일별 시세 조회 (변동성 지표 계산용 과거 데이터)
        """
        code = INDEX_CODES.get(index_name)
        if not code:
            raise ValueError(f"알 수 없는 지수명: {index_name}")

        url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-indexchartprice"
        headers = self._headers(tr_id="FHPUP02120000")

        import datetime
        end_date = datetime.datetime.now().strftime("%Y%m%d")
        start_date = (datetime.datetime.now() - datetime.timedelta(days=period_days * 2)).strftime("%Y%m%d")

        params = {
            "FID_COND_MRKT_DIV_CODE": "U",
            "FID_INPUT_ISCD": code,
            "FID_INPUT_DATE_1": start_date,
            "FID_INPUT_DATE_2": end_date,
            "FID_PERIOD_DIV_CODE": "D",
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    client = KISClient()
    result = client.get_index_price("코스피")
    print("코스피 현재가 조회 결과:")
    print(result)