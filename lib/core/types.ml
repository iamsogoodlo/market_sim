open Core

module OrderId : sig
  type t [@@deriving sexp, compare, hash]
  val create : unit -> t
  val to_string : t -> string
  val equal : t -> t -> bool
end = struct
  type t = int [@@deriving sexp, compare, hash]
  let counter = ref 0
  let create () =
    incr counter;
    !counter
  let to_string = Int.to_string
  let equal = Int.equal
end

module Side = struct
  type t = Buy | Sell [@@deriving sexp, compare, variants]

  let equal = [%compare.equal: t]

  let opposite = function
    | Buy -> Sell
    | Sell -> Buy

  let to_string = function
    | Buy -> "BUY"
    | Sell -> "SELL"
end

module OrderType = struct
  type t =
    | Limit of { price: float }
    | Market
    | Iceberg of { price: float; visible_qty: int }
  [@@deriving sexp, compare]

  let to_string = function
    | Limit { price } -> sprintf "LIMIT@%.2f" price
    | Market -> "MARKET"
    | Iceberg { price; visible_qty } ->
        sprintf "ICEBERG@%.2f(vis:%d)" price visible_qty
end

module Order = struct
  type t = {
    id: OrderId.t;
    side: Side.t;
    order_type: OrderType.t;
    quantity: int;
    remaining_qty: int;
    timestamp: Time_ns_unix.t;
    trader_id: string;
    symbol: string; (* Stock symbol, e.g., "AAPL", "MSFT" *)
  } [@@deriving sexp, fields]

  let create ~side ~order_type ~quantity ~trader_id ?(symbol="AAPL") () =
    {
      id = OrderId.create ();
      side;
      order_type;
      quantity;
      remaining_qty = quantity;
      timestamp = Time_ns_unix.now ();
      trader_id;
      symbol;
    }

  let price t = match t.order_type with
    | Limit { price } -> Some price
    | Iceberg { price; _ } -> Some price
    | Market -> None

  let is_filled t = t.remaining_qty = 0

  let reduce_qty t ~by =
    { t with remaining_qty = t.remaining_qty - by }
end

module Execution = struct
  type t = {
    buy_order_id: OrderId.t;
    sell_order_id: OrderId.t;
    price: float;
    quantity: int;
    timestamp: Time_ns_unix.t;
  } [@@deriving sexp, fields]

  let create ~buy_order_id ~sell_order_id ~price ~quantity =
    {
      buy_order_id;
      sell_order_id;
      price;
      quantity;
      timestamp = Time_ns_unix.now ();
    }
end

module MarketData = struct
  type quote = {
    bid_price: float option;
    bid_size: int;
    ask_price: float option;
    ask_size: int;
    timestamp: Time_ns_unix.t;
  } [@@deriving sexp, fields]

  type trade = {
    price: float;
    size: int;
    aggressor: Side.t;
    timestamp: Time_ns_unix.t;
  } [@@deriving sexp, fields]

  type update =
    | Quote of quote
    | Trade of trade
    | OrderBookSnapshot
  [@@deriving sexp, variants]
end

module Position = struct
  type t = {
    quantity: int;
    vwap: float;
    realized_pnl: float;
  } [@@deriving sexp, fields]

  let empty = {
    quantity = 0;
    vwap = 0.0;
    realized_pnl = 0.0;
  }

  let update t ~execution ~side =
    let qty_delta = match side with
      | Side.Buy -> execution.Execution.quantity
      | Side.Sell -> -execution.Execution.quantity
    in
    let new_qty = t.quantity + qty_delta in

    if new_qty = 0 then
      { quantity = 0; vwap = 0.0; realized_pnl = t.realized_pnl }
    else if Sign.(<>) (Int.sign new_qty) (Int.sign t.quantity) && t.quantity <> 0 then
      (* Position flip - realize P&L *)
      let closed_qty = Int.min (Int.abs qty_delta) (Int.abs t.quantity) in
      let pnl = Float.of_int closed_qty *.
                (execution.price -. t.vwap) *.
                (if t.quantity > 0 then 1.0 else -1.0) in
      let new_vwap = execution.price in
      { quantity = new_qty; vwap = new_vwap; realized_pnl = t.realized_pnl +. pnl }
    else
      (* Position increase *)
      let new_vwap =
        (t.vwap *. Float.of_int (Int.abs t.quantity) +.
         execution.price *. Float.of_int (Int.abs qty_delta)) /.
        Float.of_int (Int.abs new_qty)
      in
      { t with quantity = new_qty; vwap = new_vwap }

  let unrealized_pnl t ~mark_price =
    Float.of_int t.quantity *. (mark_price -. t.vwap)

  let total_pnl t ~mark_price =
    t.realized_pnl +. unrealized_pnl t ~mark_price
end
