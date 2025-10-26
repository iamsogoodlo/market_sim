open Core_types

module Limits : sig
  type t = {
    max_position: int;
    max_order_size: int;
    max_notional: float;
    max_loss: float;
  } [@@deriving sexp]

  val default : t
end

module RiskMetrics : sig
  type t = {
    current_position: int;
    notional_exposure: float;
    realized_pnl: float;
    unrealized_pnl: float;
    total_pnl: float;
    var_95: float option;
  } [@@deriving sexp, fields]
end

type t

val create : limits:Limits.t -> t

val check_order : t -> order:Types.Order.t -> position:Types.Position.t -> mark_price:float -> bool

val compute_metrics : t -> position:Types.Position.t -> mark_price:float -> RiskMetrics.t

val should_kill_switch : t -> metrics:RiskMetrics.t -> bool

val update_var : t -> returns:float list -> unit
