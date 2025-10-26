open Core
open Core_types

let%test_module "OrderBook Tests" = (module struct
  let%test "create empty orderbook" =
    let ob = OrderBook.create () in
    Option.is_none (OrderBook.get_bbo ob)

  let%test "add buy order" =
    let ob = OrderBook.create () in
    let order = Types.Order.create
      ~side:Types.Side.Buy
      ~order_type:(Types.OrderType.Limit { price = 100.0 })
      ~quantity:10
      ~trader_id:"test"
    in
    let ob = OrderBook.add_order ob order in
    match OrderBook.get_bbo ob with
    | Some (bid, _ask) -> Float.(bid = 100.0)
    | None -> false

  let%test "add sell order" =
    let ob = OrderBook.create () in
    let order = Types.Order.create
      ~side:Types.Side.Sell
      ~order_type:(Types.OrderType.Limit { price = 101.0 })
      ~quantity:10
      ~trader_id:"test"
    in
    let ob = OrderBook.add_order ob order in
    match OrderBook.get_bbo ob with
    | Some (_bid, ask) -> Float.(ask = 101.0)
    | None -> false

  let%test "match orders" =
    let ob = OrderBook.create () in
    let buy = Types.Order.create
      ~side:Types.Side.Buy
      ~order_type:(Types.OrderType.Limit { price = 101.0 })
      ~quantity:10
      ~trader_id:"buyer"
    in
    let sell = Types.Order.create
      ~side:Types.Side.Sell
      ~order_type:(Types.OrderType.Limit { price = 100.0 })
      ~quantity:10
      ~trader_id:"seller"
    in
    let ob = OrderBook.add_order ob buy in
    let ob = OrderBook.add_order ob sell in
    let execs, _ob = OrderBook.match_orders ob in
    List.length execs = 1

  let%test "spread calculation" =
    let ob = OrderBook.create () in
    let buy = Types.Order.create
      ~side:Types.Side.Buy
      ~order_type:(Types.OrderType.Limit { price = 100.0 })
      ~quantity:10
      ~trader_id:"buyer"
    in
    let sell = Types.Order.create
      ~side:Types.Side.Sell
      ~order_type:(Types.OrderType.Limit { price = 101.0 })
      ~quantity:10
      ~trader_id:"seller"
    in
    let ob = OrderBook.add_order ob buy in
    let ob = OrderBook.add_order ob sell in
    match OrderBook.get_spread ob with
    | Some spread -> Float.(spread = 1.0)
    | None -> false
end)

let%test_module "Position Tests" = (module struct
  let%test "empty position" =
    let pos = Types.Position.empty in
    pos.quantity = 0

  let%test "update position on buy" =
    let pos = Types.Position.empty in
    let exec = Types.Execution.create
      ~buy_order_id:(Types.OrderId.create ())
      ~sell_order_id:(Types.OrderId.create ())
      ~price:100.0
      ~quantity:10
    in
    let pos = Types.Position.update pos ~execution:exec ~side:Types.Side.Buy in
    pos.quantity = 10 && Float.(pos.vwap = 100.0)

  let%test "update position on sell" =
    let pos = Types.Position.empty in
    let exec = Types.Execution.create
      ~buy_order_id:(Types.OrderId.create ())
      ~sell_order_id:(Types.OrderId.create ())
      ~price:100.0
      ~quantity:10
    in
    let pos = Types.Position.update pos ~execution:exec ~side:Types.Side.Sell in
    pos.quantity = -10

  let%test "unrealized pnl" =
    let pos = { Types.Position.quantity = 10; vwap = 100.0; realized_pnl = 0.0 } in
    let upnl = Types.Position.unrealized_pnl pos ~mark_price:110.0 in
    Float.(upnl = 100.0)
end)

let%test_module "Strategy Tests" = (module struct
  let%test "avellaneda stoikov quote generation" =
    let params = MarketMaker.AS_Params.default in
    let quote = MarketMaker.avellaneda_stoikov_quote
      ~params
      ~mid_price:100.0
      ~inventory:0
      ~time_remaining:(Time_ns.Span.of_int_sec 1800)
    in
    Option.is_some quote
end)
