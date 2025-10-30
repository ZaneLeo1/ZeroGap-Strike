import time, httpx
from typing import Optional
from core.models import Quote, Funding
from .base import ExchangeAdapter

# Bybit 永续：BTCUSDT
# orderbook: https://api.bybit.com/v5/market/orderbook?category=linear&symbol=BTCUSDT
# funding:   https://api.bybit.com/v5/market/funding/history?category=linear&symbol=BTCUSDT&limit=1

BASE = "https://api.bybit.com"

class BybitAdapter(ExchangeAdapter):
    name = "bybit"

    def normalize_symbol(self, std_symbol: str) -> Optional[str]:
        return std_symbol

    async def fetch_quote(self, std_symbol: str) -> Optional[Quote]:
        url = f"{BASE}/v5/market/orderbook"
        params = {"category":"linear", "symbol": std_symbol}
        async with httpx.AsyncClient(timeout=0.8) as cli:
            r = await cli.get(url, params=params)
        if r.status_code != 200: return None
        j = r.json()
        r0 = (j.get("result") or {}).get("a")  # ask
        r1 = (j.get("result") or {}).get("b")  # bid
        # 有时返回结构为 {"result":{"a":[["price","size"]...],"b":[...]}}
        if not r0 or not r1: return None
        ask = float(r0[0][0]); bid = float(r1[0][0])
        return Quote(symbol=std_symbol, exchange=self.name, bid=bid, ask=ask, ts_ms=int(time.time()*1000))

    async def fetch_funding(self, std_symbol: str) -> Optional[Funding]:
        url = f"{BASE}/v5/market/funding/history"
        params = {"category":"linear", "symbol": std_symbol, "limit": 1}
        async with httpx.AsyncClient(timeout=0.8) as cli:
            r = await cli.get(url, params=params)
        if r.status_code != 200: return None
        j = r.json()
        rows = (j.get("result") or {}).get("list") or []
        rate = None
        if rows:
            try:
                rate = float(rows[0].get("fundingRate"))
            except:
                rate = None
        return Funding(symbol=std_symbol, exchange=self.name, rate=rate, ts_ms=int(time.time()*1000))