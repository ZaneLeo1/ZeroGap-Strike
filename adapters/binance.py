import time, httpx
from typing import Optional
from core.models import Quote, Funding
from .base import ExchangeAdapter

# Binance 永续：/fapi
# orderbook: https://fapi.binance.com/fapi/v1/depth?symbol=BTCUSDT&limit=5
# funding:   https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT  -> lastFundingRate

BASE = "https://fapi.binance.com"

class BinanceAdapter(ExchangeAdapter):
    name = "binance"

    def normalize_symbol(self, std_symbol: str) -> Optional[str]:
        # 标准名与binance永续一致（多数情况）
        return std_symbol

    async def fetch_quote(self, std_symbol: str) -> Optional[Quote]:
        sym = self.normalize_symbol(std_symbol)
        if not sym: return None
        url = f"{BASE}/fapi/v1/depth"
        params = {"symbol": sym, "limit": 5}
        async with httpx.AsyncClient(timeout=0.8) as cli:
            r = await cli.get(url, params=params)
        if r.status_code != 200: return None
        j = r.json()
        bids = j.get("bids") or []
        asks = j.get("asks") or []
        if not bids or not asks: return None
        bid = float(bids[0][0]); ask = float(asks[0][0])
        return Quote(symbol=std_symbol, exchange=self.name, bid=bid, ask=ask, ts_ms=int(time.time()*1000))

    async def fetch_funding(self, std_symbol: str) -> Optional[Funding]:
        sym = self.normalize_symbol(std_symbol)
        if not sym: return None
        url = f"{BASE}/fapi/v1/premiumIndex"
        params = {"symbol": sym}
        async with httpx.AsyncClient(timeout=0.8) as cli:
            r = await cli.get(url, params=params)
        if r.status_code != 200: return None
        j = r.json()
        rate = j.get("lastFundingRate")
        try:
            rate = float(rate)
        except:
            rate = None
        return Funding(symbol=std_symbol, exchange=self.name, rate=rate, ts_ms=int(time.time()*1000))