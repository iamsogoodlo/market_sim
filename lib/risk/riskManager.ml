open Core
open Core_types

module Limits = struct
  type t = {
    max_position: int;
    max_order_size: int;
    max_notional: float;
    max_loss: float;
  } [@@deriving sexp]

  let default = {
    max_position = 1000;
    max_order_size = 100;
    max_notional = 100_000.0;
    max_loss = 10_000.0;
  }
end

module RiskMetrics = struct
  type t = {
    current_position: int;
    notional_exposure: float;
    realized_pnl: float;
    unrealized_pnl: float;
    total_pnl: float;
    var_95: float option;
  } [@@deriving sexp, fields]
end

type t = {
  limits: Limits.t;
  mutable var_95: float option;
}

let create ~limits = {
  limits;
  var_95 = None;
}

let check_order t ~order ~position ~mark_price =
  let new_position = match order.Types.Order.side with
    | Buy -> position.Types.Position.quantity + order.quantity
    | Sell -> position.quantity - order.quantity
  in

  (* Check position limits *)
  let position_ok = Int.abs new_position <= t.limits.max_position in

  (* Check order size *)
  let size_ok = order.quantity <= t.limits.max_order_size in

  (* Check notional exposure *)
  let notional = Float.of_int (Int.abs new_position) *. mark_price in
  let notional_ok = Float.(notional <= t.limits.max_notional) in

  (* Check P&L limits *)
  let total_pnl = Types.Position.total_pnl position ~mark_price in
  let pnl_ok = Float.(total_pnl >= -.t.limits.max_loss) in

  position_ok && size_ok && notional_ok && pnl_ok

let compute_metrics t ~position ~mark_price =
  let current_position = position.Types.Position.quantity in
  let notional_exposure = Float.of_int (Int.abs current_position) *. mark_price in
  let realized_pnl = position.realized_pnl in
  let unrealized_pnl = Types.Position.unrealized_pnl position ~mark_price in
  let total_pnl = realized_pnl +. unrealized_pnl in

  {
    RiskMetrics.current_position;
    notional_exposure;
    realized_pnl;
    unrealized_pnl;
    total_pnl;
    var_95 = t.var_95;
  }

let should_kill_switch t ~metrics =
  (* Trigger kill switch if total P&L exceeds loss limit *)
  Float.(metrics.RiskMetrics.total_pnl < -.t.limits.max_loss) ||
  (* Or if notional exposure is too high *)
  Float.(metrics.notional_exposure > t.limits.max_notional *. 1.1)

let update_var t ~returns =
  (* Simple VaR calculation: 95th percentile of losses *)
  if List.is_empty returns then
    t.var_95 <- None
  else
    let sorted_returns = List.sort returns ~compare:Float.compare in
    let index = Float.to_int (0.05 *. Float.of_int (List.length sorted_returns)) in
    let var = List.nth sorted_returns index |> Option.value ~default:0.0 in
    t.var_95 <- Some (Float.abs var)
