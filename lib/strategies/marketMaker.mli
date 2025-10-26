open Core
open Core_types

module AS_Params : sig
  type t = {
    risk_aversion: float;
    volatility: float;
    terminal_time: Time_ns.Span.t;
    tick_size: float;
  } [@@deriving sexp]

  val default : t
end

module Quote : sig
  type t = {
    bid_price: float;
    bid_size: int;
    ask_price: float;
    ask_size: int;
  } [@@deriving sexp, fields]

  val create : bid_price:float -> bid_size:int -> ask_price:float -> ask_size:int -> t
  val to_orders : t -> trader_id:string -> Types.Order.t list
end

module Strategy : sig
  type t =
    | AvellanedaStoikov of AS_Params.t
    | SimpleSpread of { half_spread: float; size: int }
    | Custom of (state -> Quote.t option)

  and state = {
    orderbook: OrderBook.t;
    position: Types.Position.t;
    inventory: int;
    time_remaining: Time_ns.Span.t;
  }

  val sexp_of_t : t -> Sexp.t
  val compute_quotes : t -> state -> Quote.t option
end

val avellaneda_stoikov_quote :
  params:AS_Params.t ->
  mid_price:float ->
  inventory:int ->
  time_remaining:Time_ns.Span.t ->
  Quote.t option
