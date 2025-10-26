# Market Simulator - Usage Guide

## Quick Start

The Market Simulator is now running! Here's how to use it:

## 1. Web Interface

The web server is running at **http://localhost:8080**

- **Homepage**: View the order book visualization
- **WebSocket**: Connect to `ws://localhost:8080/ws` for real-time updates

To stop the server: Press `Ctrl+C` in the terminal

## 2. Using the OCaml API

### Starting the OCaml REPL

```bash
eval $(opam env)
dune utop lib
```

### Basic Order Book Operations

```ocaml
open Core;;
open Core_types;;

(* Create an empty order book *)
let ob = OrderBook.create ();;

(* Create a buy order *)
let buy_order = Types.Order.create
  ~side:Types.Side.Buy
  ~order_type:(Types.OrderType.Limit { price = 100.0 })
  ~quantity:10
  ~trader_id:"trader_1";;

(* Create a sell order *)
let sell_order = Types.Order.create
  ~side:Types.Side.Sell
  ~order_type:(Types.OrderType.Limit { price = 101.0 })
  ~quantity:10
  ~trader_id:"trader_2";;

(* Add orders to the book *)
let ob = OrderBook.add_order ob buy_order;;
let ob = OrderBook.add_order ob sell_order;;

(* Get best bid and offer *)
let bbo = OrderBook.get_bbo ob;;

(* Get mid price *)
let mid = OrderBook.get_mid_price ob;;

(* Get spread *)
let spread = OrderBook.get_spread ob;;

(* Print order book *)
OrderBook.to_string ob |> print_endline;;
```

### Matching Orders

```ocaml
(* Create overlapping orders that will match *)
let buy_order = Types.Order.create
  ~side:Types.Side.Buy
  ~order_type:(Types.OrderType.Limit { price = 101.0 })
  ~quantity:5
  ~trader_id:"buyer";;

let sell_order = Types.Order.create
  ~side:Types.Side.Sell
  ~order_type:(Types.OrderType.Limit { price = 100.0 })
  ~quantity:5
  ~trader_id:"seller";;

let ob = OrderBook.create ();;
let ob = OrderBook.add_order ob buy_order;;
let ob = OrderBook.add_order ob sell_order;;

(* Match the orders *)
let (executions, new_ob) = OrderBook.match_orders ob;;

(* Print executions *)
List.iter executions ~f:(fun exec ->
  printf "Execution: Price=%.2f Qty=%d\n"
    exec.Types.Execution.price
    exec.quantity
);;
```

### Working with Positions

```ocaml
(* Create an empty position *)
let pos = Types.Position.empty;;

(* Simulate an execution *)
let exec = Types.Execution.create
  ~buy_order_id:(Types.OrderId.create ())
  ~sell_order_id:(Types.OrderId.create ())
  ~price:100.0
  ~quantity:10;;

(* Update position with a buy *)
let pos = Types.Position.update pos ~execution:exec ~side:Types.Side.Buy;;

(* Check unrealized P&L at current market price *)
let pnl = Types.Position.unrealized_pnl pos ~mark_price:102.0;;
printf "Unrealized P&L: %.2f\n" pnl;;

(* Check total P&L *)
let total_pnl = Types.Position.total_pnl pos ~mark_price:102.0;;
printf "Total P&L: %.2f\n" total_pnl;;
```

## 3. Agent Types

The simulator supports different types of trading agents:

### Informed Traders
```ocaml
open Simulation;;

let informed_trader = Agent.create
  ~id:"informed_1"
  ~behavior:(Agent.Behavior.Informed {
    signal_strength = 0.5;  (* positive = bullish, negative = bearish *)
    trade_size = 10;
  });;
```

### Noise Traders
```ocaml
let noise_trader = Agent.create
  ~id:"noise_1"
  ~behavior:(Agent.Behavior.Noise {
    arrival_rate = 0.1;  (* probability of trading each step *)
    size_dist = (fun _ -> Random.int_incl 1 20);
  });;
```

### Momentum Traders
```ocaml
open Core_unix;;

let momentum_trader = Agent.create
  ~id:"momentum_1"
  ~behavior:(Agent.Behavior.Momentum {
    lookback = Time_ns.Span.of_int_sec 60;
    sensitivity = 0.8;
  });;
```

## 4. Order Types

### Limit Orders
```ocaml
let limit_order = Types.Order.create
  ~side:Types.Side.Buy
  ~order_type:(Types.OrderType.Limit { price = 100.0 })
  ~quantity:10
  ~trader_id:"trader_1";;
```

### Market Orders
```ocaml
let market_order = Types.Order.create
  ~side:Types.Side.Buy
  ~order_type:Types.OrderType.Market
  ~quantity:10
  ~trader_id:"trader_1";;
```

### Iceberg Orders
```ocaml
let iceberg_order = Types.Order.create
  ~side:Types.Side.Sell
  ~order_type:(Types.OrderType.Iceberg {
    price = 101.0;
    visible_qty = 5  (* only show 5 units, hide the rest *)
  })
  ~quantity:50
  ~trader_id:"trader_1";;
```

## 5. Key Features

### Order Book Features
- **Price-time priority matching**: Orders match at best price, with time priority
- **Multiple order types**: Limit, Market, Iceberg
- **Real-time matching**: Immediate order matching with execution reports
- **Market data**: BBO (best bid/offer), mid price, spread calculation

### Position Tracking
- **VWAP calculation**: Volume-weighted average price
- **Realized P&L**: Profit/loss from closed positions
- **Unrealized P&L**: Mark-to-market P&L on open positions
- **Position updates**: Automatic position tracking on executions

### Trading Agents
- **Informed traders**: Act on private signals
- **Noise traders**: Provide random liquidity
- **Momentum traders**: Follow price trends
- **Market makers**: (Avellaneda-Stoikov strategy - in development)

## 6. Restarting the Server

If you need to restart the server:

```bash
# Stop current server (Ctrl+C or)
pkill -f "server.exe"

# Rebuild if needed
eval $(opam env)
dune build server/server.exe

# Start server
dune exec server/server.exe
```

## 7. Project Structure

```
market_sim/
├── lib/
│   ├── core/          # Order book, types, core data structures
│   ├── strategies/    # Market-making algorithms
│   ├── simulation/    # Event engine, multi-agent simulation
│   └── risk/         # Risk management
├── server/           # Dream web server with WebSocket support
├── examples/         # Example simulations
└── test/            # Tests
```

## 8. Next Steps

- **Explore the web UI** at http://localhost:8080
- **Try the REPL examples** above
- **Read the README** for more details on strategies and architecture
- **Check ARCHITECTURE.md** for system design details

## Troubleshooting

### Server won't start
```bash
# Check if port 8080 is already in use
lsof -i :8080

# Kill any process using the port
kill -9 <PID>
```

### Build errors
```bash
# Rebuild from scratch
dune clean
dune build
```

### Missing dependencies
```bash
# Reinstall dependencies
eval $(opam env)
opam install . --deps-only -y
```
