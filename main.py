# main.py
import asyncio
from typing import Optional
from contextlib import asynccontextmanager
from datetime import datetime
import zoneinfo

import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import uvicorn

KST = zoneinfo.ZoneInfo("Asia/Seoul")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    TELEGRAM_BOT_TOKEN: str = Field(..., description="Telegram bot token")
    TELEGRAM_CHAT_ID: str = Field(..., description="Target chat ID")
    DEFAULT_MESSAGE: str = Field("안녕하세요! 정기 발송 메시지입니다.", description="Default text")

settings = Settings()

scheduler = AsyncIOScheduler(timezone=KST)
TELEGRAM_API = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

async def send_telegram(text: str) -> None:
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
    }
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(TELEGRAM_API, json=payload)
                data = resp.json()
                if resp.status_code == 200 and data.get("ok"):
                    return
                else:
                    raise RuntimeError(f"Telegram API error: {data}")
        except Exception as e:
            if attempt == 2:
                raise e
            await asyncio.sleep(1.5 * (attempt + 1))

async def scheduled_job():
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    text = f"[자동발송] {now} - PC 살아 있음 추후 보유수량 수익률 보내도록 수정필요"
    await send_telegram(text)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 스케줄 등록
    scheduler.add_job(scheduled_job, CronTrigger(hour=10, minute=0))  # 10:00 KST
    scheduler.add_job(scheduled_job, CronTrigger(hour=19, minute=0))  # 19:00 KST
    scheduler.start()
    try:
        yield
    finally:
        # 종료 시 스케줄러도 정리
        scheduler.shutdown(wait=False)

app = FastAPI(title="Telegram Scheduler Server", version="1.0.0", lifespan=lifespan)

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "server_time_kst": datetime.now(KST).isoformat(),
        "schedules": ["10:00 KST daily", "19:00 KST daily"],
    }

@app.get("/send-test")
async def send_test(text: Optional[str] = Query(None, description="보낼 메시지")):
    try:
        await send_telegram(text or f"[테스트] {settings.DEFAULT_MESSAGE}")
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # 스크립트로 바로 실행할 때
    uvicorn.run(app, host="0.0.0.0", port=20001)
