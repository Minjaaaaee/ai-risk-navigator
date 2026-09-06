"""
배치 작업 스케줄러 - APScheduler로 매일 자정 top-movers 갱신
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.batch.job_scan_daily import run_scan_daily

scheduler = BackgroundScheduler(timezone="Asia/Seoul")


def start_scheduler():
    scheduler.add_job(
        run_scan_daily,
        trigger=CronTrigger(hour=0, minute=0),
        id="daily_scan",
        replace_existing=True,
    )
    scheduler.start()
    print("스케줄러 시작: 매일 00:00 top-movers 스캐닝 등록됨")