# ⚡ ZeroGap-Strike v4.3 — 实时跨交易所价差监控系统  
**代号：精准重生 (Rebirth of Precision)**  

ZeroGap-Strike v4.3 是 ZeroGap 系列的重构版本，  
专注于 **多交易所（Binance / OKX / Bybit）** 之间的实时价差与资金费率监控，  
为自动化套利与量化研究提供稳定、结构化的数据引擎。

---

## 🚀 主要特性

- **异步引擎（Async Engine）**  
  基于 `httpx.AsyncClient` 实现并发抓取，默认 1 秒刷新一次。  

- **统一适配层（Adapter Layer）**  
  封装 Binance / OKX / Bybit 的 API 接口与符号差异，标准化输出。  

- **费用与净差模型（Fee & Net-Spread Model）**  
  自动扣除 Maker / Taker 手续费，显示真实套利净差。  

- **结构化 API 输出**  
  `/api/data` 提供标准 JSON 数据，可直接对接前端、Grafana 或 TradingView。  

- **可配置 YAML 文件**  
  支持自定义交易所启用、费率、币种池与轮询周期。  

---

## 🛠️ 安装步骤

```bash
git clone https://github.com/ZaneLeo1/ZeroGap-Strike.git
cd ZeroGap-Strike
pip3 install -r requirements.txt
