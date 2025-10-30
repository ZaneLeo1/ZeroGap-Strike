import time, httpx
from typing import Optional
from core.models import Quote, Funding
from .base import ExchangeAdapter

# OKX 永续：BTC-USDT-SWAP
# orderbook: https://www.okx.com/api/v5/market/books?instId=BTC-USDT-SWAP&sz=5
# funding:   https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP -> data[0].fundingRate

BASE = "https://www.okx.com"

class OkxAdapter(ExchangeAdapter):
    name = "okx"

    def normalize_symbol(self, std_symbol: str) -> Optional[str]:
        return f"{std_symbol.replace('USDT','')}-USDT-SWAP"

    async def fetch_quote(self, std_symbol: str) -> Optional[Quote]:
        iid = self.normalize_symbol(std_symbol)
        url = f"{BASE}/api/v5/market/books"
        params = {"instId": iid, "sz": 5}
        async with httpx.AsyncClient(timeout=0.8) as cli:
            r = await cli.get(url, params=params)
        if r.status_code != 200: return None
        j = r.json()
        data = j.get("data") or []
        if not data: return None
        d0 = data[0]
        bids = d0.get("bids") or []
        asks = d0.get("asks") or []
        if not bids or not asks: return None
        bid = float(bids[0][0]); ask = float(asks[0][0])
        return Quote(symbol=std_symbol, exchange=self.name, bid=bid, ask=ask, ts_ms=int(time.time()*1000))

    async def fetch_funding(self, std_symbol: str) -> Optional[Funding]:
        iid = self.normalize_symbol(std_symbol)
        url = f"{BASE}/api/v5/public/funding-rate"
        params = {"instId": iid}
        async with httpx.AsyncClient(timeout=0.8) as cli:
            r = await cli.get(url, params=params)
        if r.status_code != 200: return None
        j = r.json()
        data = j.get("data") or []
        rate = None
        if data:
            try:
                rate = float(data[0].get("fundingRate"))
            except:
                rate = None
        return Funding(symbol=std_symbol, exchange=self.name, rate=rate, ts_ms=int(time.time()*1000))s