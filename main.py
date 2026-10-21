import os
from collections import deque
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# Санах ойд дээд тал нь 10,000 лаа хадгалах
MAX_CANDLES = 10000
gold_candles = deque(maxlen=MAX_CANDLES)

# Bridge-ээс ирэх өгөгдлийн бүтэц (Pydantic model)
class CandleItem(BaseModel):
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    bid: Optional[float] = None
    ask: Optional[float] = None

class CandlePayload(BaseModel):
    symbol: str
    full_snapshot: bool = False
    candles: List[CandleItem]


# 1. Chart харуулах хуудас: /goldchart
@app.get("/goldchart", response_class=HTMLResponse)
async def get_gold_chart():
    # Та өөрийнхөө эхэнд бичсэн index.html кодоо энд шууд буцааж болно 
    # Эсвэл HTML файлаа templates хавтсанд хийж болно. Энд шууд HTML string-ээр эсвэл уншуулж болно.
    # Жишээ нь HTML файлыг шууд уншиж харуулах бол:
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h3>index.html not found on server! Please check file path.</h3>"


# 2. Bridge-ээс лааны өгөгдөл хүлээж авах эндпоинт (POST)
@app.post("/update_candles")
async def update_candles(payload: CandlePayload):
    global gold_candles
    
    if not payload.candles:
        return {"status": "ok", "total": len(gold_candles)}

    # Snapshot буюу анхны 10,000 лааг бүтнээр нь авах үед
    if payload.full_snapshot:
        gold_candles.clear()
        for c in payload.candles:
            gold_candles.append(c.dict())
        print(f"[BOOTSTRAP] Loaded initial {len(gold_candles)} candles.")
    
    # Секунд/минут тутамд шинэ лаа эсвэл одоогийн формирубч байгаа лааг шинэчлэх
    else:
        for c in payload.candles:
            c_dict = c.dict()
            if not gold_candles:
                gold_candles.append(c_dict)
                continue

            # Хэрэв open_time нь ижил бол одоо явж байгаа лааг шинэчилнэ (update)
            if gold_candles[-1]["open_time"] == c_dict["open_time"]:
                gold_candles[-1] = c_dict
            # Шинэ минут эхэлсэн бол араас нь залгана (append)
            elif c_dict["open_time"] > gold_candles[-1]["open_time"]:
                gold_candles.append(c_dict)

    return {"status": "success", "total_candles": len(gold_candles)}


# 3. JS Chart руу лааны мэдээлэл өгөх эндпоинт (GET)
@app.get("/candles/GOLD")
async def get_gold_candles():
    formatted = []
    for c in list(gold_candles):
        formatted.append([
            c["open_time"] * 1000,  # seconds -> milliseconds (JS chart-д зориулж)
            c["open"],
            c["high"],
            c["low"],
            c["close"],
            c["volume"]
        ])
    return {"candles": formatted}
