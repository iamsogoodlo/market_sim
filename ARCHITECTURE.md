# Architecture Overview

## System Design

Market Simulator follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│          Web UI (ReScript)              │
│         WebSocket Client                │
└─────────────┬───────────────────────────┘
              │ WebSocket
┌─────────────▼───────────────────────────┐
│       Dream Web Server                  │
│    (server/server.ml)                   │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│      Event Engine (Async)               │
│   (lib/simulation/eventEngine.ml)       │
└─────┬───────────────────────────────────┘
      │
      ├──────► Risk Manager ──────┐
      │     (lib/risk/)            │
      │                            ▼
      ├──────► Agents ────────► OrderBook
      │     (lib/simulation/)      │
      │                            │
      └──────► Strategies ─────────┘
           (lib/strategies/)
```

## Core Components

### 1. Type System (lib/core/types.ml)

Foundation of type safety using OCaml's advanced type system:

```ocaml
module OrderId : sig
  type t [@@deriving sexp, compare, hash]
  val create : unit -> t
end

type order_type =
  | Limit of { price: float }
  | Market
  | Iceberg of { price: float; visible_qty: int }
```

**Key Features:**
- Phantom types for compile-time safety
- Derived equality, comparison, and serialization
- Opaque types to prevent misuse

### 2. Order Book (lib/core/orderBook.ml)

High-performance matching engine using functional data structures:

```ocaml
type side_book = (float, PriceLevel.t, Float.comparator_witness) Map.t

type t = {
  bids: side_book;
  asks: side_book;
  order_map: (OrderId.t, float * Side.t) Hashtbl.t;
  executions: Execution.t list;
}
```

**Implementation:**
- Price-time priority matching
- O(log n) order insertion/cancellation
- Immutable updates with structural sharing
- Efficient depth queries

**Matching Algorithm:**
```ocaml
let rec match_loop t executions =
  match get_best_bid t, get_best_ask t with
  | Some (bid_price, _), Some (ask_price, _) when bid_price >= ask_price ->
      (* Execute at ask price (price improvement for buyer) *)
      let execution = create_execution ... in
      match_loop t' (execution :: executions)
  | _ -> (List.rev executions, t)
```

### 3. Event Engine (lib/simulation/eventEngine.ml)

Async-based event processing with priority scheduling:

```ocaml
type 'a event =
  | MarketData of market_update
  | Fill of execution
  | RiskCheck of position
  | Timer of Time_ns.t
  | Custom of 'a

type t = {
  event_queue: 'a ScheduledEvent.t Heap.t;
  subscribers: ('a event -> unit Deferred.t) list;
  running: bool;
}
```

**Features:**
- Priority queue for time-ordered events
- Subscriber pattern for event handling
- Non-blocking async execution
- Graceful shutdown

### 4. Market Making Strategies (lib/strategies/)

#### Avellaneda-Stoikov Model

Implements optimal market-making under inventory risk:

**Core Formula:**
```
Reservation Price: r = s - q * γ * σ² * T
Optimal Spread: δ = γ * σ² * T + (2/γ) * ln(1 + γ/k)
```

Where:
- `s`: mid price
- `q`: inventory
- `γ`: risk aversion
- `σ`: volatility
- `T`: time to terminal
- `k`: order arrival rate

**Implementation:**
```ocaml
let avellaneda_stoikov_quote ~params ~mid_price ~inventory ~time_remaining =
  let reservation_price =
    mid_price -. Float.of_int inventory *. gamma *. (sigma ** 2.0) *. t
  in
  let half_spread = time_component +. market_impact in
  let inventory_skew = Float.of_int inventory *. 0.001 in

  Quote.create
    ~bid_price:(reservation_price -. half_spread +. inventory_skew)
    ~ask_price:(reservation_price +. half_spread +. inventory_skew)
    ~size:...
```

### 5. Multi-Agent Framework (lib/simulation/agent.ml)

Extensible agent system for market simulation:

```ocaml
module Behavior = struct
  type t =
    | Informed of { signal_strength: float; trade_size: int }
    | Noise of { arrival_rate: float; size_dist: int -> int }
    | Momentum of { lookback: Time_ns.Span.t; sensitivity: float }
    | MarketMaker of Strategy.t
end
```

**Agent Decision Flow:**
1. Observe market state (orderbook, quotes)
2. Compute action based on behavior type
3. Submit orders to orderbook
4. Update internal state on fills

### 6. Risk Management (lib/risk/riskManager.ml)

Real-time risk monitoring and controls:

```ocaml
type limits = {
  max_position: int;
  max_order_size: int;
  max_notional: float;
  max_loss: float;
}

val check_order :
  t ->
  order:Order.t ->
  position:Position.t ->
  mark_price:float ->
  bool
```

**Checks:**
- Pre-trade position limits
- Notional exposure limits
- P&L loss limits
- Kill switch activation

### 7. Web Server (server/server.ml)

Dream-based HTTP/WebSocket server:

```ocaml
let websocket_handler =
  Dream.websocket (fun websocket ->
    let rec loop () =
      let* msg_opt = Dream.receive websocket in
      match msg_opt with
      | Some msg -> process_message msg
      | None -> Lwt.return_unit
    in
    loop ()
  )
```

**Features:**
- Real-time orderbook updates via WebSocket
- REST API for configuration
- Static file serving for UI
- CORS support for development

## Data Flow

### Order Submission Flow

```
User/Agent → Order → Risk Check → OrderBook → Matching → Executions
                ↓                                            ↓
            Rejected                                    Event Engine
                                                             ↓
                                                        Subscribers
                                                             ↓
                                                    Position Update
                                                             ↓
                                                        WebSocket
                                                             ↓
                                                           UI
```

### Market Data Flow

```
OrderBook State Change → Event → Subscribers → Agents
                          ↓                      ↓
                      WebSocket             Decision
                          ↓                      ↓
                         UI                  New Orders
```

## Concurrency Model

### Async/Lwt Integration

```ocaml
(* Async for computational tasks *)
let%bind executions = match_orders_async orderbook in

(* Lwt for I/O operations *)
let%lwt () = Dream.send websocket update in

(* Sync for pure computations *)
let spread = compute_spread orderbook in
```

**Benefits:**
- Non-blocking I/O with Lwt
- Concurrent event processing with Async
- Thread-safe state management
- Efficient scheduling

## Performance Considerations

### Order Book Efficiency

- **Maps** for sorted price levels: O(log n) operations
- **Queues** for FIFO order matching: O(1) enqueue/dequeue
- **Hashtables** for order lookup: O(1) average case
- Structural sharing minimizes allocation

### Event Processing

- Priority heap for event queue: O(log n) insertion
- Lazy evaluation for deferred computations
- Batch processing for high-frequency events

### Memory Management

- Immutable data structures with sharing
- Generational GC-friendly allocation patterns
- Avoid excessive copying with references where needed

## Testing Strategy

### Unit Tests (test/test_market_sim.ml)

```ocaml
let%test "match orders" =
  let ob = OrderBook.create () in
  let buy = create_order ~side:Buy ~price:101.0 in
  let sell = create_order ~side:Sell ~price:100.0 in
  let ob = add_order ob buy |> add_order sell in
  let execs, _ob = match_orders ob in
  List.length execs = 1
```

### Property-Based Testing (QCheck)

```ocaml
QCheck.Test.make ~count:1000
  ~name:"orderbook invariants"
  (pair order_gen order_gen)
  (fun (buy, sell) ->
    (* Property: best bid < best ask *)
    let ob = add_order empty buy |> add_order sell in
    match get_bbo ob with
    | Some (bid, ask) -> bid < ask
    | None -> true
  )
```

### Benchmarks (Core_bench)

```ocaml
let () =
  Command.run (Bench.make_command [
    Bench.Test.create ~name:"order insertion"
      (fun () -> insert_orders 10000);

    Bench.Test.create ~name:"matching"
      (fun () -> match_full_book ());
  ])
```

## Extension Points

### Custom Strategies

```ocaml
let custom_strategy = Strategy.Custom (fun state ->
  (* Your logic here *)
  Some (Quote.create ~bid_price:... ~ask_price:...)
)
```

### Custom Events

```ocaml
type my_event =
  | CustomEvent1
  | CustomEvent2

let engine = EventEngine.create () in
EventEngine.schedule engine (Custom CustomEvent1) ~at:time
```

### Custom Risk Checks

```ocaml
let my_risk_check order position =
  (* Custom risk logic *)
  check_correlation order position &&
  check_var_limits position
```

## Future Enhancements

### Phase 3: ML Integration
- Owl for numerical computation
- Adverse selection models
- Order flow toxicity detection

### Phase 4: Advanced UI
- D3.js order book visualization
- Real-time P&L charts
- Strategy backtesting interface

### Phase 5: Production Features
- PostgreSQL persistence
- Distributed simulation
- Real exchange connectors
- Low-latency optimization
