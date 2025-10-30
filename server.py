import asyncio, time, yaml, os
from typing import Dict, List, Optional, Tuple
from flask import Flask, jsonify, send_from_directory, request
from core.models import Quote, Funding, PairView
from core.aggregator import FeeBook, best_pair_view
from adapters.binance import BinanceAdapter
from adapters.okx import OkxAdapter
from adapters.bybit import BybitAdapter

app = Flask(__name__, static_url_path="/static", static_folder="static")

# --- 加载配置
with open("config/exchanges.yaml","r",encoding="utf-8") as f:
    EXCFG = yaml.safe_load(f)
with open("config/symbols.yaml","r",encoding="utf-8") as f:
    SYMCFG = yaml.safe_load(f)

POLL_MS   = int(EXCFG.get("poll_interval_ms", 1000))
TIMEOUT_MS= int(EXCFG.get("request_timeout_ms", 800))
fees = FeeBook(EXCFG)

# --- 适配器注册
adapters = []
if EXCFG["exchanges"].get("binance",{}).get("enabled",True):
    adapters.append(BinanceAdapter())
if EXCFG["exchanges"].get("okx",{}).get("enabled",True):
    adapters.append(OkxAdapter())
if EXCFG["exchanges"].get("bybit",{}).get("enabled",True):
    adapters.append(BybitAdapter())

# 最新数据缓存
latest_quotes: Dict[Tuple[str,str], Quote] = {}   # (symbol, exchange) -> Quote
latest_funding: Dict[Tuple[str,str], Funding] = {}

async def poll_once():
    symbols = SYMCFG.get("perp_symbols", [])
    tasks = []

    async def fetch_one(adp, sym):
        q = await adp.fetch_quote(sym)
        if q: latest_quotes[(sym, adp.name)] = q
        f = await adp.fetch_funding(sym)
        if f: latest_funding[(sym, adp.name)] = f

    for adp in adapters:
        for sym in symbols:
            tasks.append(fetch_one(adp, sym))

    await asyncio.gather(*tasks, return_exceptions=True)

async def polling_loop():
    gap = POLL_MS / 1000.0
    while True:
        t0 = time.perf_counter()
        try:
            await poll_once()
        except Exception:
            pass
        dt = time.perf_counter() - t0
        await asyncio.sleep(max(0.0, gap - dt))

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/data")
def api_data():
    # 简单组对：优先 binance vs okx；其次 binance vs bybit；否则任意两家
    symbols = SYMCFG.get("perp_symbols", [])
    items: List[PairView] = []
    for sym in symbols:
        # 取各家最新
        qs = {ex: latest_quotes.get((sym, ex)) for ex in ["binance","okx","bybit"]}
        fs = {ex: latest_funding.get((sym, ex)) for ex in ["binance","okx","bybit"]}
        pair = None
        # 组对顺序
        orders = [("binance","okx"), ("binance","bybit"), ("okx","bybit")]
        for a,b in orders:
            if qs.get(a) and qs.get(b):
                pair = best_pair_view(sym, qs[a], qs[b], fs.get(a), fs.get(b), fees)
                break
        if pair:
            items.append(pair.model_dump())

    # 默认按“净差最大方向”的绝对值降序
    def best_abs(x):
        return max(abs(x["net_ab_pct"]), abs(x["net_ba_pct"]))
    items.sort(key=best_abs, reverse=True)

    return jsonify({"ok": True, "updated": int(time.time()*1000), "items": items})

@app.route("/static/<path:path>")
def static_proxy(path):
    return send_from_directory("static", path)

def main():
    try:
        import uvloop
        uvloop.install()
    except Exception:
        pass
    loop = asyncio.get_event_loop()
    loop.create_task(polling_loop())
    app.run(host="0.0.0.0", port=8000, debug=False)

if __name__ == "__main__":
    main()