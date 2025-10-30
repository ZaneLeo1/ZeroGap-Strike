import math, time, yaml
from typing import Dict, List, Tuple, Optional
from core.models import Quote, Funding, PairView

def bps_to_pct(bps: float) -> float:
    return bps / 100.0  # 100 bps = 1%

class FeeBook:
    def __init__(self, cfg: dict):
        self.taker_pct = {}
        for ex, meta in (cfg.get("exchanges") or {}).items():
            if not meta.get("enabled", True): continue
            self.taker_pct[ex] = bps_to_pct(meta.get("taker_fee_bps", 7))

    def taker(self, exchange: str) -> float:
        return self.taker_pct.get(exchange, 0.001)  # 默认0.1%

def best_pair_view(sym: str, qa: Quote, qb: Quote, fa: Optional[Funding], fb: Optional[Funding], fees: FeeBook) -> PairView:
    # 两向毛差（以平均价归一）
    def pct(a, b):  # (b - a) / avg * 100
        avg = 0.5*(a+b)
        if avg <= 0: return 0.0
        return (b - a) / avg * 100.0

    # A买B卖：A用ask成交，B用bid成交
    spread_ab = pct(qa.ask, qb.bid)
    spread_ba = pct(qb.ask, qa.bid)

    # 费用（两边taker之和），以百分比%
    fee_ab = (fees.taker(qa.exchange) + fees.taker(qb.exchange)) * 100.0
    fee_ba = fee_ab

    net_ab = spread_ab - fee_ab
    net_ba = spread_ba - fee_ba

    return PairView(
        symbol=sym,
        exA=qa.exchange, exB=qb.exchange,
        spread_ab_pct=round(spread_ab, 6),
        spread_ba_pct=round(spread_ba, 6),
        net_ab_pct=round(net_ab, 6),
        net_ba_pct=round(net_ba, 6),
        fundingA=(fa.rate if fa else None),
        fundingB=(fb.rate if fb else None),
        zscore=None
    )