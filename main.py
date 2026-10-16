import os
from datetime import datetime, timezone
from threading import Lock

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict


app = FastAPI(title="GOLD Indicator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

API_KEY = os.getenv("API_KEY", "")

_lock = Lock()
_latest_data = None


class IndicatorPayload(BaseModel):
    model_config = ConfigDict(extra="allow")


def check_api_key(x_api_key: str | None):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )


@app.get("/")
def home():
    return {
        "status": "online",
        "service": "GOLD Indicator API",
        "endpoints": [
            "/health",
            "/api/indicators",
        ],
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/indicators")
def receive_indicators(
    payload: IndicatorPayload,
    x_api_key: str | None = Header(default=None),
):
    global _latest_data

    check_api_key(x_api_key)

    data = payload.model_dump()

    if not data:
        raise HTTPException(
            status_code=400,
            detail="Empty indicator data",
        )

    record = {
        "received_at": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }

    with _lock:
        _latest_data = record

    return {
        "status": "success",
        "message": "Indicator results received",
        "received_at": record["received_at"],
    }

@app.get("/api/indicators")
def get_indicators(
    # check_api_key(x_api_key) -> Энэ мөрийг хасчихвал GET хүсэлт 401 өгөхгүй нээгдэнэ
):
    with _lock:
        if _latest_data is None:
            return {
                "status": "waiting",
                "message": "No indicator results received yet",
                "data": None,
            }

        return {
            "status": "success",
            **_latest_data,
        }
