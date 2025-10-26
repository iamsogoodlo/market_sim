# Market Simulator

A sophisticated market-making simulator built with OCaml, featuring real-time order book matching, multiple trading strategies, and a web-based visualization interface.

## Features

### Core Engine
- **High-performance order book** with price-time priority matching
- **Multiple order types**: Limit, Market, Iceberg
- **Real-time execution** with microsecond timestamps
- **Position tracking** with P&L calculation

### Trading Strategies
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

### Event-Driven Architecture
- Async/Lwt-based event processing
- Scheduled events and timers
- Market data subscriptions
- Fill notifications

## Project Structure

```
market_sim/
├── lib/
│   ├── core/          # Order book, types, core data structures
│   ├── strategies/    # Market-making algorithms
│   ├── simulation/    # Event engine, multi-agent simulation
│   ├── ml/           # Machine learning components (planned)
│   └── risk/         # Risk management
├── server/           # Dream web server with WebSocket support
├── ui/              # Frontend (planned: ReScript + React)
├── data/            # Historical data, configurations
└── test/            # Tests and benchmarks
```

## Installation

### Prerequisites
- OCaml >= 5.0.0
- opam >= 2.1.0
- dune >= 3.12

### Setup

```bash
# Install dependencies
opam install . --deps-only

# Build the project
dune build

# Run tests
dune test

# Run the server
dune exec market_sim_server
```

## Usage

### Starting the Server

```bash
dune exec market_sim_server
```

Then open your browser to `http://localhost:8080`

### Using the OCaml API

```ocaml
open Core
open Market_sim

(* Create an order book *)
let orderbook = OrderBook.create ()

(* Create orders *)
let buy_order = Types.Order.create
  ~side:Types.Side.Buy
  ~order_type:(Types.OrderType.Limit { price = 100.0 })
  ~quantity:10
  ~trader_id:"trader_1"

let sell_order = Types.Order.create
  ~side:Types.Side.Sell
  ~order_type:(Types.OrderType.Limit { price = 101.0 })
  ~quantity:10
  ~trader_id:"trader_2"

(* Add to order book *)
let orderbook = OrderBook.add_order orderbook buy_order
let orderbook = OrderBook.add_order orderbook sell_order

(* Match orders *)
let executions, orderbook = OrderBook.match_orders orderbook

(* Get best bid/offer *)
let bbo = OrderBook.get_bbo orderbook
```

### Market Making Strategy

```ocaml
open Strategies

(* Create Avellaneda-Stoikov parameters *)
let params = MarketMaker.AS_Params.{
  risk_aversion = 0.1;
  volatility = 0.02;
  terminal_time = Time_ns.Span.of_int_sec 3600;
  tick_size = 0.01;
}

(* Create strategy *)
let strategy = MarketMaker.Strategy.AvellanedaStoikov params

(* Compute quotes *)
let state = {
  MarketMaker.Strategy.orderbook;
  position;
  inventory = 0;
  time_remaining = Time_ns.Span.of_int_sec 1800;
}

let quotes = MarketMaker.Strategy.compute_quotes strategy state
```

### Multi-Agent Simulation

```ocaml
open Simulation

(* Create agents *)
let market_maker = Agent.create
  ~id:"mm_1"
  ~behavior:(Agent.Behavior.MarketMaker strategy)

let informed_trader = Agent.create
  ~id:"informed_1"
  ~behavior:(Agent.Behavior.Informed {
    signal_strength = 0.5;
    trade_size = 10;
  })

(* Run simulation *)
let engine = EventEngine.create ()

(* Schedule events and run *)
Async.Thread_safe.block_on_async_exn (fun () ->
  EventEngine.run engine ~until:(Time_ns.add (Time_ns.now ()) (Time_ns.Span.of_int_sec 60))
)
```

## Development Roadmap

### Phase 1: Core Engine (Completed)
- [x] Order book implementation
- [x] Order types and matching
- [x] Position tracking
- [x] Basic strategies

### Phase 2: Event System (Completed)
- [x] Event-driven architecture
- [x] Multi-agent framework
- [x] Risk management

### Phase 3: ML Components (Planned)
- [ ] Adverse selection detection
- [ ] Order flow toxicity
- [ ] Optimal execution (TWAP/VWAP)
- [ ] Reinforcement learning agents

### Phase 4: UI Development (In Progress)
- [x] Basic web server
- [x] WebSocket support
- [ ] ReScript frontend
- [ ] Real-time order book visualization
- [ ] P&L charts
- [ ] Strategy configuration UI

### Phase 5: Advanced Features (Planned)
- [ ] Historical backtesting
- [ ] Multiple instruments
- [ ] Cross-exchange arbitrage
- [ ] Market impact models

## Architecture

### Type Safety
Uses OCaml's strong type system with GADTs for event handling:

```ocaml
type _ event =
  | MarketData : market_update -> unit event
  | RiskCheck : position -> risk_result event
```

### Efficiency
- Incremental computation for reactive updates
- Async for concurrent event processing
- Efficient data structures (Maps, Heaps, Queues)

### Testing
- Property-based testing with QCheck
- Benchmarks using Core_bench
- Integration tests for strategies

## Performance

The simulator is designed for high-throughput scenarios:
- Order book operations: O(log n)
- Event processing: Async/Lwt concurrency
- Incremental updates for efficient recomputation

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## References

- Avellaneda, M., & Stoikov, S. (2008). High-frequency trading in a limit order book
- Glosten, L. R., & Milgrom, P. R. (1985). Bid, ask and transaction prices in a specialist market
- Cartea, Á., Jaimungal, S., & Penalva, J. (2015). Algorithmic and high-frequency trading

## Contact

For questions or feedback, please open an issue on GitHub.
