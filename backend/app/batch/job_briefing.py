"""
기술1-3 - 정기 안심 브리핑
6개 체크포인트(08/09/12/15:30/17/20시)에 국내+해외 코멘터리 파이프라인 재실행
직전 체크포인트 대비 유의미한 변화가 있을 때만 알림 발송, 없으면 상태만 조용히 갱신
"""

import os
import sys
import json
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app.services.commentary import generate_index_commentary
from app.services.commentary_overseas import generate_overseas_commentary

CHECKPOINTS = ["08:00", "09:00", "12:00", "15:30", "17:00", "20:00"]

# 상태 저장 파일 (직전 체크포인트 결과 기억용)
STATE_FILE = os.path.join(os.path.dirname(__file__), ".briefing_state.json")

CHANGE_THRESHOLD_PCT = 1.0  # 직전 대비 등락률 변화폭 1%p 이상이면 알림


def _load_previous_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_state(state: dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _should_notify(index_name: str, current_change_pct: float, previous_state: dict) -> bool:
    """
    직전 체크포인트 대비 등락률 변화폭이 임계치 이상이거나,
    새로운 이벤트(3% 이상)가 발생했으면 알림 발송
    """
    prev_change_pct = previous_state.get(index_name, {}).get("change_rate_pct")

    if prev_change_pct is None:
        return abs(current_change_pct) >= 3.0  # 최초 실행이면 이벤트 기준으로만 판단

    diff = abs(current_change_pct - prev_change_pct)
    return diff >= CHANGE_THRESHOLD_PCT


def run_briefing(checkpoint_time: str = None) -> dict:
    """
    정기 브리핑 실행. checkpoint_time 없으면 현재 시각 사용.
    """
    if checkpoint_time is None:
        checkpoint_time = datetime.now().strftime("%H:%M")

    previous_state = _load_previous_state()
    new_state = {}
    results = {}

    # 국내 지수 (실시간 파이프라인 재사용)
    for index_name in ["코스피", "코스닥"]:
        result = generate_index_commentary(index_name=index_name, threshold_pct=3.0, investment_horizon="장기")
        notify = _should_notify(index_name, result["change_rate_pct"], previous_state)

        results[index_name] = {
            **result,
            "should_notify": notify,
            "checkpoint": checkpoint_time,
        }
        new_state[index_name] = {"change_rate_pct": result["change_rate_pct"]}

    # 해외 지수는 아침 체크포인트(08:00, 09:00)에서만 실행 (간밤 시황이라 장중에 계속 볼 필요 없음)
    if checkpoint_time in ["08:00", "09:00"]:
        for index_name in ["나스닥", "S&P500"]:
            result = generate_overseas_commentary(index_name=index_name, threshold_pct=3.0)
            notify = _should_notify(index_name, result["change_rate_pct"], previous_state)

            results[index_name] = {
                **result,
                "should_notify": notify,
                "checkpoint": checkpoint_time,
            }
            new_state[index_name] = {"change_rate_pct": result["change_rate_pct"]}

    _save_state(new_state)
    return results


def format_briefing_message(results: dict) -> str:
    """
    브리핑 결과를 사용자에게 보여줄 메시지 형태로 정리
    """
    lines = []
    for index_name, r in results.items():
        checkpoint = r["checkpoint"]
        if r["should_notify"]:
            lines.append(f"[{index_name} 요약 {checkpoint}] {r['change_rate_pct']}% ({r['direction']})")
            if r["is_event"]:
                # 3% 이상 실제 이벤트 -> 뉴스기반 상세 코멘터리
                lines.append(r["commentary"])
            else:
                # 3% 미만이지만 직전 체크포인트 대비 변화가 커서 알림 -> 변화 자체를 알림
                lines.append(f"직전 체크포인트 대비 변동폭이 커져 알려드립니다 (관찰 필요)")
        else:
            lines.append(f"[마지막 업데이트 {checkpoint}] {index_name} 특이사항 없음")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    # 이슈 #12 완료 기준 테스트: 같은 체크포인트를 2회 연속 실행해서
    # 1차는 알림, 2차는 변화 적으면 생략되는지 확인
    print("=== 1차 실행 (09:00 체크포인트) ===\n")
    results1 = run_briefing(checkpoint_time="09:00")
    print(format_briefing_message(results1))

    print("\n=== 2차 실행 (같은 09:00, 직전과 비교) ===\n")
    results2 = run_briefing(checkpoint_time="09:00")
    print(format_briefing_message(results2))