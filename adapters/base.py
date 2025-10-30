from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple, List
from core.models import Quote, Funding

class ExchangeAdapter(ABC):
    name: str

    @abstractmethod
    def normalize_symbol(self, std_symbol: str) -> Optional[str]:
        """把标准化的永续符号（如 BTCUSDT）映射为本所的永续名称；不存在返回None"""
        ...

    @abstractmethod
    async def fetch_quote(self, std_symbol: str) -> Optional[Quote]:
        """返回 best bid/ask（永续）"""
        ...

    @abstractmethod
    async def fetch_funding(self, std_symbol: str) -> Optional[Funding]:
        """返回资金费率；没有就 None"""
        ...