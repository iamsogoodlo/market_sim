

```markdown
# MarketSim - Quantitative Paper Trading Platform

A full-featured paper trading platform where users can develop, test, and deploy custom algorithmic trading strategies in a simulated environment powered by real-time NASDAQ market data.

---

## 🎯 Vision

MarketSim enables quantitative traders, developers, and researchers to test trading algorithms in a risk-free simulated environment with institutional-grade analytics and real market data.

**Key Goals**
- Test algorithmic trading strategies without financial risk  
- Access real-time NASDAQ market data via OpenBB  
- Deploy custom strategies in Python, OCaml, or JavaScript  
- Analyze performance with institutional-grade analytics  
- Learn quantitative finance through hands-on experimentation  

> **Note:** This is a paper trading platform only. No real money is involved.

---

## ✨ Features

### Current Features

#### Backend Infrastructure
- High-performance order book with price-time priority matching (OCaml 5.3)  
- PostgreSQL 15 for persistent storage (users, portfolios, orders, transactions)  
- Redis 7 caching layer for sub-second market data access (<1ms cache hits)  
- Real-time WebSocket updates for order execution and market data  
- Python 3.13 + OpenBB integration for live NASDAQ quotes and historical data  
- 50+ NASDAQ stocks with real-time pricing  

#### Frontend (Next.js 15)
- Modern React 19 UI with TypeScript  
- Tailwind CSS v4 + shadcn/ui for design consistency  
- Real-time dashboard connected via WebSocket  
- Collapsible sidebar navigation  
- Responsive design for desktop and mobile  

#### Quantitative Strategies (1/7 Implemented)
1. ✅ Cointegration Pairs Trading — Statistical arbitrage with mean-reversion  
2. ⏳ Ornstein-Uhlenbeck Mean Reversion  
3. ⏳ Time-Series Momentum (12-1 with vol targeting)  
4. ⏳ Cross-Sectional Value (Industry-neutral)  
5. ⏳ Quality/Profitability Composite (QMJ-style)  
6. ⏳ Earnings Surprise & Revision Drift (PEAD)  
7. ⏳ Factor-Neutral Residual Momentum  

Each strategy produces a **1–5 rating** with quantitative metrics and rationale.

#### Market Making Framework
- Avellaneda-Stoikov optimal market-making algorithm  
- Simple spread strategy for testing  
- Custom plug-in framework for user strategies  

#### Multi-Agent Simulation
- Informed traders (private signals)  
- Noise traders (random orders)  
- Momentum traders (trend following)  
- Market makers (liquidity providers)  

#### Risk Management
- Position limits and exposure controls  
- Real-time P&L tracking  
- Value-at-Risk (VaR) analytics  
- Kill switch for risk breaches  

---

## 📡 Data Providers & API Sources

MarketSim integrates multiple data APIs for broad, reliable, and cost-effective coverage across equities, ETFs, options, futures, FX, and crypto.

### 🌍 Global Equities & ETFs
| Provider | Coverage | Free Tier | Notes |
|-----------|-----------|-----------|-------|
| **Alpha Vantage** | U.S. & global stocks, ETFs | ✅ Yes | Free tier (25 req/day); ideal for basic equity & FX data |
| **Finnhub** | Global equities, fundamentals, news | ✅ Yes | Free real-time data; ideal for research and education |
| **Twelve Data** | Stocks, ETFs, FX, crypto | ✅ Yes | 800 req/day, 8 calls/min; broad coverage |
| **Yahoo Finance** | Global stocks, ETFs, options | ⚠️ Partial | Free/delayed via unofficial APIs |
| **Marketstack** | 30,000+ tickers | ⚠️ Limited | Free/paid mix; delayed equities |

### 🧠 U.S. Options & Global Derivatives
| Provider | Coverage | Free Tier | Notes |
|-----------|-----------|-----------|-------|
| **Databento** | U.S. options, futures | ❌ No | Professional-grade paid feed |
| **Massive** | U.S. options chain | ⚠️ Partial | Free tier limited; paid for full depth |
| **QuoteMedia / ORATS** | Options analytics | ❌ No | Advanced vol/Greeks data |
| **CME Group API** | Futures/options | ❌ No | Exchange-paid feed |

### ₿ Crypto
| Provider | Coverage | Free Tier | Notes |
|-----------|-----------|-----------|-------|
| **CoinAPI** | 200+ exchanges | ⚠️ Limited | Free developer plan; paid for tick-level data |
| **CoinDesk API** | Digital assets | ✅ Partial | Free for basic endpoints |
| **Amberdata** | Blockchain & DeFi | ⚠️ Partial | Limited free endpoints |

### 💱 Forex
| Provider | Coverage | Free Tier | Notes |
|-----------|-----------|-----------|-------|
| **Alpha Vantage** | FX pairs | ✅ Yes | Free & reliable for major pairs |
| **Finnhub** | FX, crypto, commodities | ✅ Yes | Real-time quotes |
| **Twelve Data** | FX and multi-asset | ✅ Yes | Covers major currencies |
| **QUODD / Xignite** | Institutional FX | ❌ No | Paid |

### 📊 Fundamental & Historical Data
| Provider | Coverage | Free Tier | Notes |
|-----------|-----------|-----------|-------|
| **Financial Modeling Prep (FMP)** | Fundamentals, macro | ✅ Yes | Free for limited endpoints |
| **EOD Historical Data** | 30+ years, 70+ exchanges | ⚠️ Partial | Free for small scope; full coverage paid |

---

### Integration Architecture

- Modular `IDataProvider` interface (Python/OCaml hybrid)  
- Redis cache (<1 ms query latency)  
- Routing logic dynamically selects API by asset class, uptime, and rate limits  
- Automatic failover between APIs  
- Start with free tiers, scale up to institutional feeds  

---

---

## 📈 Development Roadmap

### Phase 1: Core Infrastructure ✅
- [x] OCaml order matching engine  
- [x] PostgreSQL schema  
- [x] WebSocket real-time updates  
- [x] User authentication  
- [x] Portfolio tracking  
- [x] Real NASDAQ data via OpenBB  
- [x] 50+ NASDAQ symbols  
- [x] Modern Next.js frontend  

### Phase 2: Advanced Analytics (In Progress)
- [x] Redis caching layer  
- [x] Cointegration pairs strategy  
- [ ] 6 remaining quant strategies  
- [ ] Real-time order book visualization  
- [ ] P&L and drawdown analytics  
- [ ] Risk dashboard (Sharpe, Sortino, VaR)  

### Phase 3: Strategy Development Platform 🚀
- [ ] Strategy configuration UI & visual builder  
- [ ] Backtesting engine with historical replay  
- [ ] Slippage & latency modeling  
- [ ] Algorithm upload (Python, OCaml, JS)  
- [ ] Paper trading API with REST + WebSocket endpoints  
- [ ] Performance attribution and factor analytics  
- [ ] Multi-timeframe & multi-symbol backtesting  
- [ ] Real-time risk dashboard with VaR & exposure metrics  
- [ ] Strategy lifecycle management (create, pause, delete)  
- [ ] Integrated AI strategy copilot  

### Phase 4: Quantitative Infrastructure Expansion ⚙️
- [ ] Multi-asset support (stocks, options, futures, crypto, FX)  
- [ ] Cross-exchange arbitrage detection  
- [ ] Market impact and slippage simulation  
- [ ] Fama-French factor modeling & momentum layer  
- [ ] Monte Carlo risk simulation engine  
- [ ] ML strategy framework (TensorFlow, PyTorch)  
- [ ] Cloud backtesting infrastructure (Dockerized)  
- [ ] Scalable sandbox environments  
- [ ] Telemetry & performance monitoring dashboard  
- [ ] REST + GraphQL API for developer integration  

### Phase 5: Social & Collaborative Ecosystem 🌐
- [ ] Public strategy leaderboard  
- [ ] Strategy marketplace (share/fork algorithms)  
- [ ] Paper trading competitions  
- [ ] Copy-trading simulation (non-financial)  
- [ ] Collaborative notebooks (Python + Markdown)  
- [ ] Team access & version control via Git  
- [ ] Educational quant content hub  
- [ ] Community discussion boards  
- [ ] Strategy rating & reputation system  
- [ ] Integrated analytics sharing  

---

## 🧠 Technology Stack

| Layer | Technology | Purpose |
|-------|-------------|----------|
| Core Engine | OCaml 5.3 | Order matching |
| Data Layer | PostgreSQL 15 | Persistent storage |
| Cache Layer | Redis 7 | Market data caching |
| Web Server | Dream | HTTP & WebSocket |
| Market Data | Python 3.13 + OpenBB | Live NASDAQ feeds |
| Quant Engine | NumPy, Pandas, SciPy, statsmodels | Strategy analytics |
| Frontend | Next.js 15, React 19, Tailwind v4 | Modern responsive UI |

---

## 🧪 Example Usage

### Market Data
```bash
python3 server/market_data_cache.py quote AAPL
python3 server/market_data_cache.py historical AAPL 1mo
python3 server/market_data_cache.py stats
````

### Quant Strategies

```bash
python3 server/quant_engine/pairs_trading.py AAPL
# Output: Rating (1–5), z-score, p-value, half-life, rationale
```

### OCaml Order Book

```ocaml
let buy_order = Types.Order.create
  ~side:Types.Side.Buy
  ~order_type:(Types.OrderType.Limit { price = 100.0 })
  ~quantity:10
  ~trader_id:"trader_1"
  ~symbol:"AAPL"
  ()
```

---

## 🧩 Testing

```bash
dune test
dune exec test/benchmarks.exe
```

---

## 📚 Documentation

* [README_VISION.md](./README_VISION.md) – Platform vision
* API Documentation – Coming soon
* Strategy Guide – Coming soon

---

## 🤝 Contributing

Contributions welcome! Focus areas:

* New quantitative strategies
* Performance optimization
* UI/UX enhancements
* Documentation
* Test coverage

---

## 📝 License

MIT License – See LICENSE file for details.

---

## ⚠️ Disclaimer

**PAPER TRADING ONLY**
No real capital is traded.
Paper results do not guarantee real-world returns.

---

Built with ❤️ for quantitative traders, developers, and researchers.
