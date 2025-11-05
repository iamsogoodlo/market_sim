# MarketSim - Quantitative Paper Trading Platform

A full-featured paper trading platform where users can develop, test, and deploy custom algorithmic trading strategies in a simulated environment powered by real-time NASDAQ market data.

## 🎯 Vision

MarketSim enables quantitative traders, developers, and researchers to test trading algorithms in a risk-free simulated environment with institutional-grade analytics and real market data.

**Key Goals:**
- Test algorithmic trading strategies without financial risk
- Access real-time NASDAQ market data via OpenBB
- Deploy custom strategies in Python, OCaml, or JavaScript
- Analyze performance with institutional-grade analytics
- Learn quantitative finance through hands-on experimentation

> **Note:** This is a paper trading platform only. No real money is involved.

## ✨ Features

### Current Features

#### Backend Infrastructure
- **High-performance order book** with price-time priority matching (OCaml 5.3)
- **PostgreSQL 15** for persistent storage (users, portfolios, orders, transactions)
- **Redis 7** caching layer for sub-second market data access (<1ms cache hits)
- **Real-time WebSocket** updates for order execution and market data
- **Python 3.13 + OpenBB** integration for live NASDAQ quotes and historical data
- **50+ NASDAQ stocks** with real-time pricing

#### Frontend (Next.js 15)
- **Modern React 19** UI with TypeScript
- **Beautiful animated interface** with Tailwind CSS v4 and shadcn/ui
- **Collapsible sidebar navigation** with smooth animations
- **Real-time dashboard** with WebSocket connection to backend
- **Responsive design** for desktop and mobile

#### Quantitative Strategies (1/7 Implemented)
1. ✅ **Cointegration Pairs Trading** - Statistical arbitrage with mean-reversion
2. ⏳ Ornstein-Uhlenbeck Mean Reversion
3. ⏳ Time-Series Momentum (12-1 with vol targeting)
4. ⏳ Cross-Sectional Value (Industry-neutral)
5. ⏳ Quality/Profitability Composite (QMJ-style)
6. ⏳ Earnings Surprise & Revision Drift (PEAD)
7. ⏳ Factor-Neutral Residual Momentum

Each strategy produces a **1-5 rating scale** with quantitative metrics and rationale.

### Trading Strategies (Market Making)
- **Avellaneda-Stoikov**: Optimal market-making with inventory risk
- **Simple spread**: Basic market-making strategy
- **Custom strategies**: Extensible strategy framework

### Multi-Agent Simulation
- **Informed traders**: Act on private signals
- **Noise traders**: Random order flow
- **Momentum traders**: Follow price trends
- **Market makers**: Provide liquidity with sophisticated pricing

### Risk Management
- Position limits and exposure controls
- Real-time P&L tracking
- Value-at-Risk (VaR) calculation
- Kill switch for risk breaches

## 🏗️ Architecture

```
market_sim/
├── frontend/              # Next.js 15 + React 19 + TypeScript
│   ├── app/              # App router pages
│   ├── components/       # UI components (shadcn/ui)
│   └── lib/              # Utilities
├── server/               # OCaml Dream server + Python services
│   ├── server.ml         # Main OCaml web server (WebSocket)
│   ├── stock_data.py     # OpenBB market data fetcher
│   ├── market_data_cache.py  # Redis caching layer
│   └── quant_engine/     # 7 quantitative strategies (Python)
├── lib/
│   ├── core/            # Order book, types, core data structures
│   ├── strategies/      # Market-making algorithms (OCaml)
│   ├── simulation/      # Event engine, multi-agent simulation
│   └── risk/            # Risk management
└── docs/                # Documentation
```

## 🚀 Quick Start

### Prerequisites
- **OCaml** >= 5.3.0
- **Python** >= 3.13
- **PostgreSQL** >= 15
- **Redis** >= 7
- **Node.js** >= 18
- **opam** >= 2.1.0

### Installation

1. **Install OCaml dependencies:**
```bash
opam install . --deps-only
dune build
```

2. **Install Python dependencies:**
```bash
pip install openbb-platform yfinance pandas numpy scipy statsmodels scikit-learn redis
```

3. **Start PostgreSQL:**
```bash
# Create database
createdb market_sim

# Initialize schema (from previous session)
psql market_sim < schema.sql
```

4. **Start Redis:**
```bash
brew services start redis  # macOS
# or
redis-server  # Linux
```

5. **Install and start frontend:**
```bash
cd frontend
npm install
npm run dev  # Runs on http://localhost:3000
```

6. **Start OCaml backend:**
```bash
# Terminal 1: Start OCaml server
eval $(opam env)
dune exec server/server.exe  # Runs on http://localhost:8080
```

### Access the Platform

- **Frontend**: http://localhost:3000 (Beautiful UI with sidebar)
- **Dashboard**: http://localhost:3000/dashboard (Real-time stats)
- **Legacy UI**: http://localhost:8080/app (Original brokerage UI)

## 📊 Technology Stack

### Backend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Core Engine | OCaml 5.3 + Core | Order matching, business logic |
| Database | PostgreSQL 15 | Persistent storage |
| Cache | Redis 7 | Market data (5s quote TTL, 1h historical) |
| Web Server | Dream | HTTP/WebSocket |
| Market Data | Python 3.13 + OpenBB | Real-time quotes, historical data |
| Quant Engine | NumPy, Pandas, SciPy, statsmodels | Strategy calculations |

### Frontend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | Next.js 15 (App Router) | React SSR/SSG |
| UI | shadcn/ui + Tailwind CSS v4 | Component library |
| State | React Hooks | Client state |
| Charts | Chart.js (planned) | Data visualization |
| Real-time | WebSocket | Live updates |
| Animation | Framer Motion | UI transitions |

## 🎓 Usage Examples

### Viewing Real-Time Market Data

```python
# Check cached stock quote (sub-second response)
python3 server/market_data_cache.py quote AAPL

# View historical data
python3 server/market_data_cache.py historical AAPL 1mo

# Cache statistics
python3 server/market_data_cache.py stats
```

### Testing Quantitative Strategies

```python
# Test cointegration pairs trading strategy
python3 server/quant_engine/pairs_trading.py AAPL

# Output: Rating (1-5), z-score, p-value, half-life, rationale
```

### OCaml Order Book API

```ocaml
open Core
open Market_sim

(* Create an order book *)
let orderbook = OrderBook.create ()

(* Create orders with symbol *)
let buy_order = Types.Order.create
  ~side:Types.Side.Buy
  ~order_type:(Types.OrderType.Limit { price = 100.0 })
  ~quantity:10
  ~trader_id:"trader_1"
  ~symbol:"AAPL"
  ()

(* Add to order book and match *)
let orderbook = OrderBook.add_order orderbook buy_order
let executions, orderbook = OrderBook.match_orders orderbook
```

## 📈 Development Roadmap

See [README_VISION.md](./README_VISION.md) for detailed technical specifications.

### Phase 1: Core Infrastructure ✅
- [x] OCaml order matching engine
- [x] PostgreSQL database schema
- [x] WebSocket real-time updates
- [x] User authentication system
- [x] Portfolio tracking
- [x] Real market data via OpenBB
- [x] 50+ NASDAQ stocks
- [x] Next.js frontend with modern UI

### Phase 2: Advanced Analytics (In Progress)
- [x] Redis caching layer
- [x] First quantitative strategy (Cointegration Pairs)
- [ ] Remaining 6 quantitative strategies
- [ ] Real-time order book visualization
- [ ] P&L charts with drawdown analysis
- [ ] Risk metrics dashboard (Sharpe, Sortino, max DD, VaR)

### Phase 3: Strategy Development Platform
- [ ] Strategy configuration UI with visual builder
- [ ] Backtesting engine with historical data
- [ ] Algorithm upload system (Python/OCaml/JS)
- [ ] Paper trading API for custom strategies
- [ ] Performance attribution analysis
- [ ] Multi-timeframe analysis (1m, 5m, 15m, 1h, 1d)

### Phase 4: Advanced Features
- [ ] Multiple asset classes (stocks, options, futures, crypto)
- [ ] Cross-exchange arbitrage detection
- [ ] Market impact models (price slippage simulation)
- [ ] Factor models (Fama-French 5-factor + momentum)
- [ ] Monte Carlo simulations for risk analysis
- [ ] Machine learning integration (TensorFlow/PyTorch)

### Phase 5: Social & Competitive
- [ ] Public strategy leaderboard
- [ ] Strategy marketplace (share/sell algorithms)
- [ ] Paper trading competitions
- [ ] Social trading (copy successful strategies)
- [ ] Educational content (quant finance tutorials)

## 🧪 Testing

```bash
# Run OCaml tests
dune test

# Run benchmarks
dune exec test/benchmarks.exe
```

## 📚 Documentation

- **[README_VISION.md](./README_VISION.md)** - Complete platform vision and strategy specifications
- **API Documentation** (coming soon)
- **Strategy Guide** (coming soon)

## 🤝 Contributing

Contributions are welcome! Areas of focus:
- New quantitative strategies
- Performance optimizations
- UI/UX improvements
- Documentation
- Test coverage

Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

**Built with:**
- [OpenBB](https://openbb.co/) - Financial data platform
- [Dream](https://aantron.github.io/dream/) - OCaml web framework
- [Next.js](https://nextjs.org/) - React framework
- [shadcn/ui](https://ui.shadcn.com/) - Component library

**Inspired by academic research from:**
- AQR Capital Management
- Cliff Asness, David Kabiller, John Liew
- Eugene Fama, Kenneth French
- Narasimhan Jegadeesh, Sheridan Titman

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

## ⚠️ Risk Disclaimer

**PAPER TRADING ONLY**: This platform uses simulated money. No real trading occurs. Performance in paper trading does not guarantee real-world results.

---

**Built with ❤️ for quantitative traders, developers, and researchers.**
