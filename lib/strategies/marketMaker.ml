open Core
open Core_types

module AS_Params = struct
  type t = {
    risk_aversion: float;
    volatility: float;
    terminal_time: Time_ns.Span.t;
    tick_size: float;
  } [@@deriving sexp]

  let default = {
    risk_aversion = 0.1;
    volatility = 0.02;
    terminal_time = Time_ns.Span.of_int_sec 3600;
    tick_size = 0.01;
  }
end

module Quote = struct
  type t = {
    bid_price: float;
    bid_size: int;
    ask_price: float;
    ask_size: int;
  } [@@deriving sexp, fields]

  let create ~bid_price ~bid_size ~ask_price ~ask_size =
    { bid_price; bid_size; ask_price; ask_size }

  let to_orders t ~trader_id =
    let bid = Types.Order.create
      ~side:Types.Side.Buy
      ~order_type:(Types.OrderType.Limit { price = t.bid_price })
      ~quantity:t.bid_size
      ~trader_id
    in
    let ask = Types.Order.create
      ~side:Types.Side.Sell
      ~order_type:(Types.OrderType.Limit { price = t.ask_price })
      ~quantity:t.ask_size
      ~trader_id
    in
    [bid; ask]
end

let avellaneda_stoikov_quote ~params ~mid_price ~inventory ~time_remaining =
  let open AS_Params in
  let gamma = params.risk_aversion in
  let sigma = params.volatility in
  let t = Time_ns.Span.to_sec time_remaining in
  let capital_t = Time_ns.Span.to_sec params.terminal_time in

  if Float.(t <= 0.0) then None
  else
    (* Reservation price: r = s - q * gamma * sigma^2 * T *)
    let reservation_price =
      mid_price -. Float.of_int inventory *. gamma *. (sigma ** 2.0) *. capital_t
    in

    (* Optimal spread: delta = gamma * sigma^2 * T + (2/gamma) * ln(1 + gamma/k) *)
    (* Simplified without order arrival rate k, using fixed spread component *)
    let time_component = gamma *. (sigma ** 2.0) *. t in
    let half_spread = time_component +. (2.0 /. gamma) *. Float.log (1.0 +. gamma /. 2.0) in

    (* Inventory skew: adjust spread based on inventory *)
    let inventory_skew = Float.of_int inventory *. 0.001 in

    let bid_price = Float.round_decimal
      (reservation_price -. half_spread +. inventory_skew)
      ~decimal_digits:2
    in
    let ask_price = Float.round_decimal
      (reservation_price +. half_spread +. inventory_skew)
      ~decimal_digits:2
    in

    (* Size based on confidence - reduce size as inventory grows *)
    let base_size = 10 in
    let inventory_factor = Float.max 0.1 (1.0 -. Float.abs (Float.of_int inventory) /. 100.0) in
    let size = Float.to_int (Float.of_int base_size *. inventory_factor) in

    Some (Quote.create
      ~bid_price
      ~bid_size:size
      ~ask_price
      ~ask_size:size)

module Strategy = struct
  type state = {
    orderbook: OrderBook.t;
    position: Types.Position.t;
    inventory: int;
    time_remaining: Time_ns.Span.t;
  }

  type t =
    | AvellanedaStoikov of AS_Params.t
    | SimpleSpread of { half_spread: float; size: int }
    | Custom of (state -> Quote.t option)

  let sexp_of_t = function
    | AvellanedaStoikov params ->
        Sexp.List [Sexp.Atom "AvellanedaStoikov"; AS_Params.sexp_of_t params]
    | SimpleSpread { half_spread; size } ->
        Sexp.List [
          Sexp.Atom "SimpleSpread";
          Sexp.List [
            Sexp.List [Sexp.Atom "half_spread"; sexp_of_float half_spread];
            Sexp.List [Sexp.Atom "size"; sexp_of_int size];
          ]
        ]
    | Custom _ -> Sexp.Atom "Custom"

  let compute_quotes strategy state =
    match strategy with
    | AvellanedaStoikov params ->
        (match OrderBook.get_mid_price state.orderbook with
        | None -> None
        | Some mid_price ->
            avellaneda_stoikov_quote
              ~params
              ~mid_price
              ~inventory:state.inventory
              ~time_remaining:state.time_remaining)

    | SimpleSpread { half_spread; size } ->
        (match OrderBook.get_mid_price state.orderbook with
        | None -> None
        | Some mid_price ->
            Some (Quote.create
              ~bid_price:(mid_price -. half_spread)
              ~bid_size:size
              ~ask_price:(mid_price +. half_spread)
              ~ask_size:size))

    | Custom f -> f state
end
