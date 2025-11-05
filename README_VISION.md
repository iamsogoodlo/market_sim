# MarketSim - Quantitative Paper Trading Platform

## 🎯 Vision

MarketSim is evolving into a **full-featured paper trading platform** where users can develop, test, and deploy custom algorithmic trading strategies in a simulated environment powered by real-time market data.

### Core Mission
Enable quantitative traders, developers, and researchers to:
- **Test trading algorithms** in a risk-free simulated environment
- **Access real market data** via OpenBB/yfinance integration
- **Deploy custom strategies** written in Python, OCaml, or JavaScript
- **Analyze performance** with institutional-grade analytics
- **Learn quantitative finance** through hands-on experimentation

---

## 🏗️ Current Architecture

### Backend (Production-Ready)
- **OCaml 5.3** market simulator with order matching engine
- **PostgreSQL 15** for persistence (users, portfolios, orders, transactions)
- **Dream** web framework with WebSocket support
- **Python 3.13** + **OpenBB** for real-time market data
- **Real NASDAQ stocks** with live quotes and historical charts

### Frontend (In Development)
- **Next.js 15** + **React 19** + **TypeScript**
- **Tailwind CSS** + **shadcn/ui** components
- **Framer Motion** animations
- **Chart.js** for data visualization

---

## 🚀 Roadmap to Paper Trading Platform

### Phase 1: Core Infrastructure ✅
- [x] OCaml order matching engine
- [x] PostgreSQL database schema
- [x] WebSocket real-time updates
- [x] User authentication system
- [x] Portfolio tracking
- [x] Real market data via OpenBB
- [x] 50+ NASDAQ stocks

### Phase 2: Advanced Analytics (Next)
- [ ] **Redis caching layer** for sub-second market data access
- [ ] **7 Quantitative Strategies** (Python + OCaml):
  1. Cointegration Pairs Trading (Statistical Arbitrage)
  2. Ornstein-Uhlenbeck Mean Reversion
  3. Time-Series Momentum (12-1 with vol targeting)
  4. Cross-Sectional Value (Industry-neutral)
  5. Quality/Profitability Composite (QMJ-style)
  6. Earnings Surprise & Revision Drift (PEAD)
  7. Factor-Neutral Residual Momentum
- [ ] **Real-time order book visualization**
- [ ] **P&L charts** with drawdown analysis
- [ ] **Risk metrics dashboard** (Sharpe, Sortino, max DD, VaR)

### Phase 3: Strategy Development Platform
- [ ] **Strategy Configuration UI** with visual builder
- [ ] **Backtesting engine** with historical data
- [ ] **Algorithm upload system** (Python/OCaml/JS)
- [ ] **Paper trading API** for custom strategies
- [ ] **Performance attribution** analysis
- [ ] **Multi-timeframe analysis** (1m, 5m, 15m, 1h, 1d)

### Phase 4: Advanced Features
- [ ] **Multiple asset classes** (stocks, options, futures, crypto)
- [ ] **Cross-exchange arbitrage** detection
- [ ] **Market impact models** (price slippage simulation)
- [ ] **Factor models** (Fama-French 5-factor + momentum)
- [ ] **Monte Carlo simulations** for risk analysis
- [ ] **Machine learning integration** (TensorFlow/PyTorch models)

### Phase 5: Social & Competitive
- [ ] **Public strategy leaderboard**
- [ ] **Strategy marketplace** (share/sell algorithms)
- [ ] **Paper trading competitions**
- [ ] **Social trading** (copy successful strategies)
- [ ] **Educational content** (quant finance tutorials)

---

## 📊 Quantitative Strategies - Technical Specification

### Strategy Rating System
Each strategy produces:
- **Rating**: 1-5 scale (1=SELL, 3=HOLD, 5=BUY)
- **Key Metrics**: Quantitative values (z-scores, percentiles, etc.)
- **Rationale**: One-line explanation
- **Overall Signal**: Weighted composite of all strategies

### 1. Cointegration Pairs Trading
**Theory**: Identify cointegrated stock pairs; trade mean-reversion of the spread.

**Implementation**:
- Find best peer via Engle-Granger/Johansen cointegration test (p<0.05)
- Regress log(P_i) = α + β·log(P_j) + ε
- Compute spread z-score with 60-90 day rolling window
- Calculate half-life from AR(1) model

**Rating Scale**:
- z ≤ -2.0 → 5 (strong buy)
- -2.0 < z ≤ -1.0 → 4
- -1.0 < z < 1.0 → 3 (neutral)
- 1.0 ≤ z < 2.0 → 2
- z ≥ 2.0 → 1 (strong sell)

**Output**:
```json
{
  "rating": 5,
  "metrics": {
    "peer": "MSFT",
    "z_score": -2.3,
    "p_value": 0.018,
    "half_life_days": 18
  },
  "rationale": "Spread cheap vs MSFT (-2.3σ), HL~18d ⇒ fast reversion"
}
```

### 2. Ornstein-Uhlenbeck Mean Reversion
**Theory**: Model price as mean-reverting stochastic process.

**Implementation**:
- Fit discrete OU process (AR(1) on log prices)
- Estimate κ (mean-reversion speed), μ (long-term mean), σ (volatility)
- Half-life HL = ln(2)/κ
- Compute deviation z = (x_t - μ) / σ_dev

**Rating Scale**:
- HL ∈ [5,60] and z ≤ -1.5 → 5
- HL ∈ [5,60] and -1.5 < z ≤ -0.5 → 4
- -0.5 < z < 0.5 → 3
- HL outside [5,60] → cap at 3 unless z ≤ -2.5

### 3. Time-Series Momentum (12-1)
**Theory**: Past winners continue to outperform (Jegadeesh & Titman, 1993).

**Implementation**:
- 12-month return skipping last month (to avoid reversal)
- Cross-sectional z-score
- Vol-targeting: position size = min(1, σ*/σ_20d) where σ*=20%

**Rating Scale**:
- z ≥ 1.5 → 5
- 1.0 ≤ z < 1.5 → 4
- -1.0 < z < 1.0 → 3
- -1.5 < z ≤ -1.0 → 2
- z ≤ -1.5 → 1

### 4. Cross-Sectional Value (Industry-Neutral)
**Theory**: Cheap stocks outperform expensive ones within industries.

**Implementation**:
- Within GICS industry peers (≥15 stocks)
- Z-scores of: EV/EBITDA (-), P/B (-), P/E (-), P/FCF (-), Sales/EV (-)
- Composite V = mean(aligned z-scores)
- Convert to industry percentile p_V

**Rating Scale**:
- p_V ≥ 80 → 5
- 65 ≤ p_V < 80 → 4
- 35 ≤ p_V < 65 → 3
- 20 ≤ p_V < 35 → 2
- p_V < 20 → 1

### 5. Quality/Profitability (QMJ-Style)
**Theory**: High-quality firms earn superior risk-adjusted returns.

**Implementation**:
- Industry-neutral z-scores on:
  - Gross Profits / Assets (+)
  - ROIC (+)
  - Operating Margin stability (+, lower std dev → higher)
  - Accruals (-, (ΔWC + ΔNCO)/Assets)
  - Asset growth (-)
  - Net issuance (-)
- Composite percentile p_Q

**Rating Scale**: Same as Value (percentile-based)

### 6. Earnings Surprise & Revision Drift
**Theory**: Post-Earnings Announcement Drift (PEAD) + analyst revision momentum.

**Implementation**:
- SUE = (EPS_actual - EPS_consensus) / σ(surprises last 8Q)
- Revision breadth = (% upgrades - % downgrades) last 30d
- Composite E = 0.6·SUE + 0.4·z(breadth)

**Rating Scale**:
- E ≥ 1.5 → 5
- 1.0 ≤ E < 1.5 → 4
- -0.5 < E < 1.0 → 3
- -1.0 < E ≤ -0.5 → 2
- E ≤ -1.0 → 1

### 7. Factor-Neutral Residual Momentum
**Theory**: Momentum unexplained by Fama-French factors has predictive power.

**Implementation**:
- Daily regression: r_t = α + β'·f_t + ε_t
- Factors: MKT, SMB, HML, MOM, RMW, CMA
- Residual momentum m_{6,1} = Σ monthly residuals (t-12 to t-2)
- Short-term reversal rev1 = - Σ residuals (t-1)
- R = 0.7·z(m_{6,1}) + 0.3·z(rev1)

**Rating Scale**: Same as TS Momentum

---

## 🛠️ Technology Stack

### Backend
| Component | Technology | Purpose |
|---|---|---|
| Core Engine | OCaml 5.3 + Core | Order matching, business logic |
| Database | PostgreSQL 15 | Persistent storage |
| Cache | Redis 7 | Market data, quotes |
| Web Server | Dream (OCaml) | HTTP/WebSocket |
| Market Data | Python 3.13 + OpenBB | Real-time quotes, historical data |
| Quant Engine | Python (NumPy, Pandas, SciPy) | Strategy calculations |

### Frontend
| Component | Technology | Purpose |
|---|---|---|
| Framework | Next.js 15 (App Router) | React SSR/SSG |
| UI | shadcn/ui + Tailwind | Component library |
| State | React Query + Zustand | Server/client state |
| Charts | TradingView Lightweight + Chart.js | Price charts, analytics |
| Real-time | WebSocket + SWR | Live updates |
| Animation | Framer Motion | UI transitions |

### Infrastructure
| Component | Technology | Purpose |
|---|---|---|
| Container | Docker + Docker Compose | Dev/prod deployment |
| Reverse Proxy | Nginx | Load balancing |
| Monitoring | Prometheus + Grafana | Metrics, alerts |
| Logging | Loki | Centralized logs |

---

## 📁 Project Structure

```
market_sim/
├── backend/
│   ├── ocaml/              # Core market simulator
│   │   ├── lib/core/       # Order book, types
│   │   ├── lib/strategies/ # Trading strategies (OCaml)
│   │   ├── lib/risk/       # Risk management
│   │   ├── server/         # Dream web server
│   │   └── test/
│   └── python/
│       ├── quant_engine/   # 7 quant strategies
│       │   ├── pairs.py
│       │   ├── ou_mr.py
│       │   ├── ts_mom.py
│       │   ├── value.py
│       │   ├── quality.py
│       │   ├── earnings.py
│       │   └── resid_mom.py
│       ├── data/           # Market data fetchers
│       ├── backtest/       # Backtesting engine
│       └── api/            # FastAPI wrapper
├── frontend/
│   ├── app/                # Next.js app router
│   │   ├── (auth)/         # Login/signup
│   │   ├── (dashboard)/    # Main app
│   │   │   ├── portfolio/
│   │   │   ├── strategies/
│   │   │   ├── backtest/
│   │   │   └── analytics/
│   │   └── api/            # API routes
│   ├── components/
│   │   ├── ui/             # shadcn components
│   │   ├── charts/         # Chart components
│   │   ├── order-book/     # Order book viz
│   │   └── strategy/       # Strategy builder
│   └── lib/
│       ├── hooks/          # React hooks
│       ├── utils/          # Utilities
│       └── stores/         # Zustand stores
├── cache/
│   └── redis/              # Redis config
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.ocaml
│   ├── Dockerfile.python
│   └── Dockerfile.frontend
└── docs/
    ├── API.md              # API documentation
    ├── STRATEGIES.md       # Strategy details
    └── DEPLOYMENT.md       # Deployment guide
```

---

## 🎓 Educational Value

This platform serves as a **learning tool** for:
- **Quantitative Finance**: Implement academic research papers
- **Algorithm Development**: Test trading ideas without risk
- **Software Engineering**: Full-stack TypeScript/OCaml/Python
- **Data Science**: Work with real market data
- **System Design**: Build scalable real-time systems

---

## 🔐 Risk Disclaimer

**PAPER TRADING ONLY**: This platform uses simulated money. No real trading occurs. Performance in paper trading does not guarantee real-world results.

---

## 📝 License

MIT License - See LICENSE file

---

## 🤝 Contributing

We welcome contributions! Areas of focus:
- New quantitative strategies
- Performance optimizations
- UI/UX improvements
- Documentation
- Test coverage

See CONTRIBUTING.md for guidelines.

---

## 🌟 Acknowledgments

Built with:
- [OpenBB](https://openbb.co/) - Financial data platform
- [Dream](https://aantron.github.io/dream/) - OCaml web framework
- [Next.js](https://nextjs.org/) - React framework
- [shadcn/ui](https://ui.shadcn.com/) - Component library

Inspired by academic research from:
- AQR Capital Management
- Cliff Asness, David Kabiller, John Liew
- Eugene Fama, Kenneth French
- Narasimhan Jegadeesh, Sheridan Titman

---

**Built with ❤️ for quantitative traders, developers, and researchers.**
