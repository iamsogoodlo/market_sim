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

let get_holdings (user_id : int) =
  with_connection (fun conn ->
    let query = Printf.sprintf
      "SELECT symbol, quantity, avg_cost FROM holdings WHERE user_id = %d ORDER BY symbol"
      user_id
    in
    let result = conn#exec query in
    let holdings = List.init result#ntuples ~f:(fun i ->
      let symbol = result#getvalue i 0 in
      let quantity = Int.of_string (result#getvalue i 1) in
      let avg_cost = Float.of_string (result#getvalue i 2) in
      `Assoc [
        ("symbol", `String symbol);
        ("quantity", `Int quantity);
        ("avgCost", `Float avg_cost);
      ]
    ) in
    Lwt.return (`List holdings)
  )

let get_cash_balance (user_id : int) =
  with_connection (fun conn ->
    let query = Printf.sprintf
      "SELECT cash_balance FROM users WHERE id = %d"
      user_id
    in
    let result = conn#exec query in
    if result#ntuples > 0 then
      Lwt.return (Float.of_string (result#getvalue 0 0))
    else
      Lwt.return 100000.0 (* Default cash balance *)
  )

let update_cash_balance (user_id : int) (amount : float) =
  with_connection (fun conn ->
    let query = Printf.sprintf
      "UPDATE users SET cash_balance = cash_balance + %.2f WHERE id = %d"
      amount user_id
    in
    let _ = conn#exec query in
    Lwt.return_unit
  )

let get_holding (user_id : int) (symbol : string) =
  with_connection (fun conn ->
    let query = Printf.sprintf
      "SELECT quantity, avg_cost FROM holdings WHERE user_id = %d AND symbol = '%s'"
      user_id symbol
    in
    let result = conn#exec query in
    if result#ntuples > 0 then
      let quantity = Int.of_string (result#getvalue 0 0) in
      let avg_cost = Float.of_string (result#getvalue 0 1) in
      Lwt.return (Some (quantity, avg_cost))
    else
      Lwt.return None
  )

let update_holding (user_id : int) (symbol : string) (quantity : int) (price : float) =
  with_connection (fun conn ->
    (* First check if holding exists *)
    let%lwt existing = get_holding user_id symbol in
    match existing with
    | Some (old_qty, old_avg_cost) ->
        (* Update existing holding *)
        let new_qty = old_qty + quantity in
        if Int.(new_qty <= 0) then
          (* Remove holding if quantity is zero or negative *)
          let query = Printf.sprintf
            "DELETE FROM holdings WHERE user_id = %d AND symbol = '%s'"
            user_id symbol
          in
          let _ = conn#exec query in
          Lwt.return_unit
        else
          (* Calculate new average cost *)
          let new_avg_cost =
            if Int.(quantity > 0) then
              (* Buying: calculate weighted average *)
              ((old_avg_cost *. Float.of_int old_qty) +. (price *. Float.of_int quantity)) /. Float.of_int new_qty
            else
              (* Selling: keep old average cost *)
              old_avg_cost
          in
          let query = Printf.sprintf
            "UPDATE holdings SET quantity = %d, avg_cost = %.2f WHERE user_id = %d AND symbol = '%s'"
            new_qty new_avg_cost user_id symbol
          in
          let _ = conn#exec query in
          Lwt.return_unit
    | None ->
        (* Create new holding *)
        if Int.(quantity > 0) then
          let query = Printf.sprintf
            "INSERT INTO holdings (user_id, symbol, quantity, avg_cost) VALUES (%d, '%s', %d, %.2f)"
            user_id symbol quantity price
          in
          let _ = conn#exec query in
          Lwt.return_unit
        else
          (* Cannot sell what you don't have *)
          Lwt.return_unit
  )

let record_transaction (user_id : int) (symbol : string) (action : string) (quantity : int) (price : float) =
  with_connection (fun conn ->
    let total = price *. Float.of_int quantity in
    let query = Printf.sprintf
      "INSERT INTO transactions (user_id, symbol, action, quantity, price, total) \
       VALUES (%d, '%s', '%s', %d, %.2f, %.2f)"
      user_id symbol action quantity price total
    in
    let _ = conn#exec query in
    Lwt.return_unit
  )

let execute_trade (user_id : int) (symbol : string) (action : string) (quantity : int) (price : float) =
  (* Execute trade atomically *)
  with_connection (fun conn ->
    try%lwt
      (* Start transaction *)
      let _ = conn#exec "BEGIN" in

      (* Check if trade is valid *)
      let%lwt cash_balance = get_cash_balance user_id in
      let total_cost = price *. Float.of_int quantity in

      match action with
      | "buy" ->
          (* Check if user has enough cash *)
          if Float.(total_cost > cash_balance) then begin
            let _ = conn#exec "ROLLBACK" in
            Lwt.return (Error "Insufficient funds")
          end else begin
            (* Deduct cash *)
            let%lwt () = update_cash_balance user_id (-.total_cost) in
            (* Add to holdings *)
            let%lwt () = update_holding user_id symbol quantity price in
            (* Record transaction *)
            let%lwt () = record_transaction user_id symbol action quantity price in
            (* Commit transaction *)
            let _ = conn#exec "COMMIT" in
            Lwt.return (Ok "Trade executed successfully")
          end
      | "sell" ->
          (* Check if user has enough shares *)
          let%lwt holding_opt = get_holding user_id symbol in
          (match holding_opt with
          | Some (current_qty, _) when Int.(current_qty >= quantity) ->
              (* Add cash *)
              let%lwt () = update_cash_balance user_id total_cost in
              (* Remove from holdings *)
              let%lwt () = update_holding user_id symbol (-quantity) price in
              (* Record transaction *)
              let%lwt () = record_transaction user_id symbol action quantity price in
              (* Commit transaction *)
              let _ = conn#exec "COMMIT" in
              Lwt.return (Ok "Trade executed successfully")
          | Some (current_qty, _) ->
              let _ = conn#exec "ROLLBACK" in
              Lwt.return (Error (Printf.sprintf "Insufficient shares. You have %d shares" current_qty))
          | None ->
              let _ = conn#exec "ROLLBACK" in
              Lwt.return (Error "You don't own any shares of this stock"))
      | _ ->
          let _ = conn#exec "ROLLBACK" in
          Lwt.return (Error "Invalid action")
    with
    | e ->
        let _ = conn#exec "ROLLBACK" in
        Lwt.return (Error (Printf.sprintf "Trade failed: %s" (Exn.to_string e)))
  )
