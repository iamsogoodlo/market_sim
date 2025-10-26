open Core
open Core_types
open Strategies

module Behavior = struct
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

let create ~id ~behavior = {
  id;
  behavior;
  position = Types.Position.empty;
  active_orders = [];
}

let decide_action t ~orderbook ~market_data =
  match t.behavior with
  | Informed { signal_strength; trade_size } ->
      (* Informed trader acts on private signal *)
      (match OrderBook.get_mid_price orderbook with
      | None -> []
      | Some mid_price ->
          let side = if Float.(signal_strength > 0.0) then
            Types.Side.Buy
          else
            Types.Side.Sell
          in
          let limit_price = if Types.Side.equal side Types.Side.Buy then
            mid_price *. (1.0 +. Float.abs signal_strength *. 0.01)
          else
            mid_price *. (1.0 -. Float.abs signal_strength *. 0.01)
          in
          [Types.Order.create
            ~side
            ~order_type:(Types.OrderType.Limit { price = limit_price })
            ~quantity:trade_size
            ~trader_id:t.id])

  | Noise { arrival_rate; size_dist } ->
      (* Noise trader submits random orders *)
      if Float.(Random.float 1.0 < arrival_rate) then
        let side = if Random.bool () then Types.Side.Buy else Types.Side.Sell in
        let size = size_dist (Random.int 100) in
        (match OrderBook.get_bbo orderbook with
        | None -> []
        | Some (bid, ask) ->
            let price = match side with
              | Buy -> bid *. (1.0 +. Random.float 0.001)
              | Sell -> ask *. (1.0 -. Random.float 0.001)
            in
            [Types.Order.create
              ~side
              ~order_type:(Types.OrderType.Limit { price })
              ~quantity:size
              ~trader_id:t.id])
      else
        []

  | Momentum { lookback = _; sensitivity } ->
      (* Momentum trader follows price trends *)
      (match market_data with
      | None -> []
      | Some quote ->
          match quote.Types.MarketData.bid_price, quote.Types.MarketData.ask_price with
          | Some bid, Some ask ->
              let _ = (bid +. ask) /. 2.0 in
              let momentum_signal = sensitivity *. Random.float 1.0 in
              let side = if Float.(momentum_signal > 0.5) then
                Types.Side.Buy
              else
                Types.Side.Sell
              in
              [Types.Order.create
                ~side
                ~order_type:(Types.OrderType.Limit {
                  price = if Types.Side.equal side Types.Side.Buy then ask else bid
                })
                ~quantity:10
                ~trader_id:t.id]
          | _ -> [])

  | MarketMaker strategy ->
      (* Market maker uses sophisticated strategy *)
      let state = {
        MarketMaker.Strategy.orderbook;
        position = t.position;
        inventory = t.position.quantity;
        time_remaining = Time_ns.Span.of_int_sec 3600;
      } in
      (match MarketMaker.Strategy.compute_quotes strategy state with
      | None -> []
      | Some quote ->
          MarketMaker.Quote.to_orders quote ~trader_id:t.id)

let update_position t ~execution ~side =
  t.position <- Types.Position.update t.position ~execution ~side

let cancel_all_orders t =
  let orders = t.active_orders in
  t.active_orders <- [];
  orders
