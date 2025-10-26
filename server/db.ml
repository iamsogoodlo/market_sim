open Core
open Core_types

let connection_string = "host=localhost dbname=market_sim"

let with_connection f =
  let conn = new Postgresql.connection ~conninfo:connection_string () in
  Lwt.finalize
    (fun () -> f conn)
    (fun () -> conn#finish; Lwt.return_unit)

let save_order (order : Types.Order.t) =
  with_connection (fun conn ->
    let order_id = Types.OrderId.to_string order.id in
    let side = match order.side with
      | Types.Side.Buy -> "buy"
      | Types.Side.Sell -> "sell"
    in
    let (order_type, price) = match order.order_type with
      | Types.OrderType.Market -> ("market", None)
      | Types.OrderType.Limit { price } -> ("limit", Some price)
      | Types.OrderType.Iceberg _ -> ("market", None) (* Treat as market for now *)
    in
    let price_str = match price with
      | Some p -> Float.to_string p
      | None -> "NULL"
    in
    let query = Printf.sprintf
      "INSERT INTO orders (order_id, side, order_type, price, quantity, trader_id, symbol) \
       VALUES ('%s', '%s', '%s', %s, %d, '%s', '%s') \
       ON CONFLICT (order_id) DO NOTHING"
      order_id side order_type price_str order.quantity order.trader_id order.symbol
    in
    let _ = conn#exec query in
    Lwt.return_unit
  )

let save_execution (exec : Types.Execution.t) =
  with_connection (fun conn ->
    let query = Printf.sprintf
      "INSERT INTO executions (price, quantity) VALUES (%f, %d)"
      exec.price exec.quantity
    in
    let _ = conn#exec query in
    Lwt.return_unit
  )

let load_active_orders () =
  with_connection (fun conn ->
    let query = "SELECT order_id, side, order_type, price, quantity, trader_id, symbol FROM orders WHERE status = 'active' ORDER BY created_at" in
    let result = conn#exec query in
    let orders = List.init result#ntuples ~f:(fun i ->
      let _order_id_str = result#getvalue i 0 in
      let side = match result#getvalue i 1 with
        | "buy" -> Types.Side.Buy
        | "sell" -> Types.Side.Sell
        | _ -> Types.Side.Buy
      in
      let order_type = match result#getvalue i 2 with
        | "market" -> Types.OrderType.Market
        | "limit" ->
            let price = Float.of_string (result#getvalue i 3) in
            Types.OrderType.Limit { price }
        | _ -> Types.OrderType.Market
      in
      let quantity = Int.of_string (result#getvalue i 4) in
      let trader_id = result#getvalue i 5 in
      let symbol = result#getvalue i 6 in

      (* Create order with the stored ID *)
      let order = Types.Order.create ~side ~order_type ~quantity ~trader_id ~symbol () in
      (* Note: We can't set the exact ID from DB, but orders will be recreated in order *)
      order
    ) in
    Lwt.return orders
  )

let mark_order_executed (order_id : Types.OrderId.t) =
  with_connection (fun conn ->
    let order_id_str = Types.OrderId.to_string order_id in
    let query = Printf.sprintf
      "UPDATE orders SET status = 'executed' WHERE order_id = '%s'"
      order_id_str
    in
    let _ = conn#exec query in
    Lwt.return_unit
  )

let clear_all_orders () =
  with_connection (fun conn ->
    let _ = conn#exec "DELETE FROM orders" in
    let _ = conn#exec "DELETE FROM executions" in
    Lwt.return_unit
  )
