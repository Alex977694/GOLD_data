import os
from collections import deque
from flask import Flask, request, jsonify

app = Flask(__name__)

# Санах ойд дээд тал нь 10,000 лаа хадгална (Хамгийн хуучин нь автоматаар хасагдана)
MAX_CANDLES = 10000
gold_candles = deque(maxlen=MAX_CANDLES)

@app.route('/update_candles', methods=['POST'])
def update_candles():
    global gold_candles
    data = request.json
    if not data or "candles" not in data:
        return jsonify({"status": "error", "message": "No candle data provided"}), 400

    incoming_candles = data.get("candles", [])
    is_snapshot = data.get("full_snapshot", False)

    if not incoming_candles:
        return jsonify({"status": "ok", "count": len(gold_candles)})

    # 1. Анхны 10,000 лааны snapshot ирвэл шууд deque-г шинэчлэх
    if is_snapshot:
        gold_candles.clear()
        for c in incoming_candles:
            gold_candles.append(c)
        print(f"[BOOTSTRAP] Loaded initial {len(gold_candles)} candles.")
    
    # 2. Секунд/минут тутамд сүүлийн 1 лааны шинэчлэлт ирэх үед
    else:
        for c in incoming_candles:
            if not gold_candles:
                gold_candles.append(c)
                continue

            # Хэрэв open_time нь ижил байвал формирубч байгаа сүүлийн лааг update хийнэ
            if gold_candles[-1]["open_time"] == c["open_time"]:
                gold_candles[-1] = c
            # Хэрэв шинэ минут эхэлж open_time нь их болсон байвал шинэ лаа болгож араас нь залгана
            elif c["open_time"] > gold_candles[-1]["open_time"]:
                gold_candles.append(c)

    return jsonify({"status": "success", "total_candles": len(gold_candles)}), 200


@app.route('/candles/GOLD', methods=['GET'])
def get_gold_candles():
    """ Metachart.js-ийн fetch(`/candles/GOLD?interval=1`) х хүсэлтэд хариулах эндпоинт """
    # Metachart.js [time_ms, open, high, low, close, volume] хэлбэртэй массив хүлээдэг
    formatted = []
    for c in list(gold_candles):
        formatted.append([
            c["open_time"] * 1000, # seconds -> milliseconds
            c["open"],
            c["high"],
            c["low"],
            c["close"],
            c["volume"]
        ])
    return jsonify({"candles": formatted})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
