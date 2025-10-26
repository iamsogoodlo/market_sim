open Core
open Core_types
open Strategies

module Behavior : sig
  type t =
    | Informed of { signal_strength: float; trade_size: int }
    | Noise of { arrival_rate: float; size_dist: int -> int }
    | Momentum of { lookback: Time_ns.Span.t; sensitivity: float }
    | MarketMaker of MarketMaker.Strategy.t
  [@@deriving sexp_of]
end

type t = {
  id: string;
  behavior: Behavior.t;
  mutable position: Types.Position.t;
  mutable active_orders: Types.OrderId.t list;
} [@@deriving sexp_of, fields]

val create : id:string -> behavior:Behavior.t -> t

val decide_action :
  t ->
  orderbook:OrderBook.t ->
  market_data:Types.MarketData.quote option ->
  Types.Order.t list

val update_position : t -> execution:Types.Execution.t -> side:Types.Side.t -> unit

val cancel_all_orders : t -> Types.OrderId.t list
