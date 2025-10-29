#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZeroGap-Strike v4.2 — Exchange Direct Stable
- 多交易所行情直连（Binance、OKX、Bybit）
- 每60s动态更新币池；币池内每1s刷新盘口与资金费率
- 支持 config/ 下 YAML 配置文件
- 输出 /api/data 供前端展示
"""

import threading, time, math, requests, yaml, os, numpy as np
from collections import defaultdict, deque
from datetime import datetime, timezone
from flask import Flask, jsonify, send_from_directory, request

# ========= 读取配置 =========
BASE_DIR = os.path.dirname(__file__)
with open(os.path.join(BASE_DIR, "config/exchanges.yaml"), "r", encoding="utf-8") as f:
    EX_CFG = yaml.safe_load(f)
with open(os.path.join(BASE_DIR, "config/symbols.yaml"), "r", encoding="utf-8") as f:
    INIT_SYMBOLS = yaml.safe_load(f).get("symbols", [])

ENABLED_EXCHANGES = [ex for ex, v in EX_CFG.items() if v.get("enabled", True)]

HOST, PORT = "0.0.0.0", 8000
FETCH_INTERVAL_SEC, POOL_UPDATE_INTERVAL, WINDOW_SEC_DEFAULT, MAX_POOL_SIZE = 1, 60, 300, 20
TIMEOUT = 6

ring_prices = defaultdict(lambda: defaultdict(lambda: deque(maxlen=6000)))
ring_funding = defaultdict(lambda: defaultdict(lambda: deque(maxlen=14400)))
current_pool, lock = INIT_SYMBOLS.copy(), threading.Lock()

def now_ms(): return int(time.time() * 1000)
def now_str(): return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
def mid(b,a): 
    try:
        b,a=float(b),float(a)
        if b>0<a>=b: return (a+b)/2
    except: pass
    return None

# ========= 各交易所快照 =========
def fetch_binance_snapshot():
    out={}
    try:
        bt=requests.get("https://fapi.binance.com/fapi/v1/ticker/bookTicker",timeout=TIMEOUT).json()
        tick24={x["symbol"]:x for x in requests.get("https://fapi.binance.com/fapi/v1/ticker/24hr",timeout=TIMEOUT).json()}
        for it in bt:
            s=it["symbol"]
            if not s.endswith("USDT"): continue
            fr=None
            try:
                pr=requests.get("https://fapi.binance.com/fapi/v1/premiumIndex",params={"symbol":s},timeout=TIMEOUT).json()
                if "lastFundingRate" in pr: fr=float(pr["lastFundingRate"])
            except: pass
            qv=float(tick24.get(s,{}).get("quoteVolume",0))
            out[s]={"exchange":"binance","bid":it["bidPrice"],"ask":it["askPrice"],"funding":fr,"qv":qv}
    except: pass
    return out

def fetch_okx_snapshot():
    out={}
    try:
        r=requests.get("https://www.okx.com/api/v5/market/tickers",params={"instType":"SWAP"},timeout=TIMEOUT).json()
        for it in r.get("data",[]):
            inst=it.get("instId")
            if not inst or "-USDT-" not in inst: continue
            sym=inst.split("-")[0]+"USDT"
            fr=None
            try:
                f=requests.get("https://www.okx.com/api/v5/public/funding-rate",params={"instId":inst},timeout=TIMEOUT).json()
                fr=float(f.get("data",[{}])[0].get("fundingRate",0))
            except: pass
            out[sym]={"exchange":"okx","bid":it["bidPx"],"ask":it["askPx"],"funding":fr,"qv":float(it.get("volCcy24h",0))}
    except: pass
    return out

def fetch_bybit_snapshot():
    out={}
    try:
        r=requests.get("https://api.bybit.com/v5/market/tickers",params={"category":"linear"},timeout=TIMEOUT).json()
        for it in r.get("result",{}).get("list",[]):
            s=it["symbol"]
            if not s.endswith("USDT"): continue
            fr=None
            try:
                f=requests.get("https://api.bybit.com/v5/market/funding/history",params={"category":"linear","symbol":s,"limit":1},timeout=TIMEOUT).json()
                fr=float(f.get("result",{}).get("list",[{}])[0].get("fundingRate",0))
            except: pass
            out[s]={"exchange":"bybit","bid":it["bid1Price"],"ask":it["ask1Price"],"funding":fr,"qv":float(it.get("turnover24h",0))}
    except: pass
    return out

EX_FUNCS={"binance":fetch_binance_snapshot,"okx":fetch_okx_snapshot,"bybit":fetch_bybit_snapshot}

# ========= 币池更新 =========
def pool_updater():
    global current_pool
    while True:
        try:
            merged={}
            for ex in ENABLED_EXCHANGES:
                snap=EX_FUNCS.get(ex,lambda:{})()
                for sym,row in snap.items():
                    merged.setdefault(sym,{})[ex]=row
            scored=[]
            for sym,mp in merged.items():
                if len(mp)<2: continue
                mids=[mid(r["bid"],r["ask"]) for r in mp.values() if r.get("bid")]
                mids=[m for m in mids if m]
                if len(mids)<2: continue
                s_bp=(max(mids)-min(mids))/(sum(mids)/len(mids))*10000
                vol=sum(float(r.get("qv",0)) for r in mp.values())
                scored.append((sym,s_bp*math.log10(vol+2)))
            new=[s for s,_ in sorted(scored,key=lambda x:-x[1])[:MAX_POOL_SIZE]]
            if new!=current_pool:
                current_pool=new
                print(f"📊 Pool update ({len(new)}): {new}")
        except Exception as e:
            print("⚠️ pool_updater error:",e)
        time.sleep(POOL_UPDATE_INTERVAL)

# ========= 数据刷新 =========
def fetch_loop():
    while True:
        try:
            with lock: pool=list(current_pool)
            if not pool: time.sleep(1);continue
            exdata={ex:EX_FUNCS.get(ex,lambda:{})() for ex in ENABLED_EXCHANGES}
            ts=now_ms()
            with lock:
                for sym in pool:
                    for ex,sd in exdata.items():
                        r=sd.get(sym)
                        if not r: continue
                        m=mid(r["bid"],r["ask"])
                        if m: ring_prices[sym][ex].append((ts,m))
                        f=r.get("funding")
                        if isinstance(f,(int,float)): ring_funding[sym][ex].append((ts,f))
        except: pass
        time.sleep(FETCH_INTERVAL_SEC)

# ========= API =========
app=Flask(__name__,static_url_path="/static",static_folder="static")
@app.route("/")
def index(): return send_from_directory("static","index.html")

@app.route("/api/data")
def data():
    window=int(request.args.get("window",WINDOW_SEC_DEFAULT))
    cutoff=now_ms()-window*1000
    items=[]
    with lock:
        for sym,exmap in ring_prices.items():
            if sym not in current_pool or len(exmap)<2: continue
            exs=sorted(exmap.keys(),key=lambda k:len(exmap[k]),reverse=True)
            if len(exs)<2: continue
            exA,exB=exs[0],exs[1]
            midA=exmap[exA][-1][1]; midB=exmap[exB][-1][1]
            avg=(midA+midB)/2; spread=(midB-midA)/avg*100
            sa=[v for t,v in exmap[exA] if t>=cutoff]; sb=[v for t,v in exmap[exB] if t>=cutoff]
            n=min(len(sa),len(sb))
            if n>1:
                spreads=[(sb[-1-i]-sa[-1-i])/((sb[-1-i]+sa[-1-i])/2)*100 for i in range(n)]
                mu=np.mean(spreads); std=np.std(spreads,ddof=1)
                z=(spread-mu)/std if std>1e-9 else None
            else: mu,std,z=None,None,None
            fA=fB=None
            fm=ring_funding.get(sym,{})
            if fm.get(exA): fA=fm[exA][-1][1]
            if fm.get(exB): fB=fm[exB][-1][1]
            favg=None
            vals=[v for v in (fA,fB) if isinstance(v,(int,float))]
            if vals: favg=sum(vals)/len(vals)
            items.append({"symbol":sym,"exA":exA,"exB":exB,"midA":midA,"midB":midB,
                          "spread_pct":round(spread,6),
                          "avg_spread_pct":None if mu is None else round(mu,6),
                          "zscore":None if z is None else round(z,3),
                          "fundingA":fA,"fundingB":fB,"funding_avg":favg})
    items.sort(key=lambda x:abs(x["spread_pct"]),reverse=True)
    return jsonify({"ok":True,"updated":now_str(),"pool":current_pool,"items":items})

if __name__=="__main__":
    threading.Thread(target=pool_updater,daemon=True).start()
    threading.Thread(target=fetch_loop,daemon=True).start()
    print("🚀 ZeroGap-Strike v4.2 启动")
    app.run(host=HOST,port=PORT,debug=False)
