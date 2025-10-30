from pydantic import BaseModel
from typing import Optional
from dataclasses import dataclass

class Quote(BaseModel):
    symbol: str
    exchange: str
    bid: float
    ask: float
    ts_ms: int

class Funding(BaseModel):
    symbol: str
    exchange: str
    rate: Optional[float] = None
    ts_ms: int

class PairView(BaseModel):
    symbol: str
    exA: str
    exB: str
    # 两向可成交毛差（%）
    spread_ab_pct: float       # A买 B卖
    spread_ba_pct: float       # B买 A卖
    # 扣费后的净差（%）
    net_ab_pct: float
    net_ba_pct: float
    # 资金费率（最新可得）
    fundingA: Optional[float] = None
    fundingB: Optional[float] = None
    # 统计占位（下一步填MAD/EWMA）
    zscore: Optional[float] = None