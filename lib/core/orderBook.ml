open Core

module PriceLevel = struct
  type t = {
    price: float;
    orders: Types.Order.t Queue.t;
    total_qty: int;
  } [@@deriving sexp]

  let create price = {
    price;
    orders = Queue.create ();
    total_qty = 0;
  }

  let add_order t order =
    Queue.enqueue t.orders order;
    { t with total_qty = t.total_qty + order.Types.Order.remaining_qty }

  let remove_order t order_id =
    let new_queue = Queue.create () in
    let removed = ref None in
    Queue.iter t.orders ~f:(fun order ->
      if Types.OrderId.equal order.Types.Order.id order_id then
        removed := Some order
      else
        Queue.enqueue new_queue order
    );
    match !removed with
    | None -> None
    | Some ord ->
        Some ({ t with
                orders = new_queue;
                total_qty = t.total_qty - ord.remaining_qty
              }, ord)

  let is_empty t = Queue.is_empty t.orders
end

type side_book = (float, PriceLevel.t, Float.comparator_witness) Map.t

type t = {
  bids: side_book;
  asks: side_book;
  order_map: (Types.OrderId.t, float * Types.Side.t) Hashtbl.t;
  executions: Types.Execution.t list;
}

let create () = {
  bids = Map.empty (module Float);
  asks = Map.empty (module Float);
  order_map = Hashtbl.create (module Types.OrderId);
  executions = [];
}

let add_order_to_side side_book order price =
  Map.update side_book price ~f:(function
    | None -> PriceLevel.create price |> fun level -> PriceLevel.add_order level order
    | Some level -> PriceLevel.add_order level order
  )

let add_order t order =
  match Types.Order.price order with
  | None -> t (* Market orders handled differently *)
  | Some price ->
      let side_book, side = match order.side with
        | Buy -> t.bids, Types.Side.Buy
        | Sell -> t.asks, Types.Side.Sell
      in
      let new_side_book = add_order_to_side side_book order price in
      Hashtbl.set t.order_map ~key:order.id ~data:(price, side);
      match order.side with
      | Buy -> { t with bids = new_side_book }
      | Sell -> { t with asks = new_side_book }

let cancel_order t order_id =
  match Hashtbl.find t.order_map order_id with
  | None -> None
  | Some (price, side) ->
      let side_book = match side with
        | Buy -> t.bids
        | Sell -> t.asks
      in
      match Map.find side_book price with
      | None -> None
      | Some level ->
          match PriceLevel.remove_order level order_id with
          | None -> None
          | Some (new_level, _removed_order) ->
              let new_side_book =
                if PriceLevel.is_empty new_level then
                  Map.remove side_book price
                else
                  Map.set side_book ~key:price ~data:new_level
              in
              Hashtbl.remove t.order_map order_id;
              let t' = match side with
                | Buy -> { t with bids = new_side_book }
                | Sell -> { t with asks = new_side_book }
              in
              Some t'

let get_best_bid t =
  Map.max_elt t.bids |> Option.map ~f:(fun (price, level) ->
    (price, level.PriceLevel.total_qty)
  )

let get_best_ask t =
  Map.min_elt t.asks |> Option.map ~f:(fun (price, level) ->
    (price, level.PriceLevel.total_qty)
  )

let get_bbo t =
  match get_best_bid t, get_best_ask t with
  | Some (bid, _), Some (ask, _) -> Some (bid, ask)
  | _ -> None

let get_spread t =
  match get_bbo t with
  | Some (bid, ask) -> Some (ask -. bid)
  | None -> None

let get_mid_price t =
  match get_bbo t with
  | Some (bid, ask) -> Some ((bid +. ask) /. 2.0)
  | None -> None

let get_depth side_book levels =
  Map.to_alist side_book
  |> (fun lst -> List.take lst levels)
  |> List.map ~f:(fun (price, level) -> (price, level.PriceLevel.total_qty))

let get_bid_depth t levels =
  get_depth t.bids levels |> List.rev

let get_ask_depth t levels =
  get_depth t.asks levels

let get_volume_at_price t ~side ~price =
  let side_book = match side with
    | Types.Side.Buy -> t.bids
    | Types.Side.Sell -> t.asks
  in
  Map.find side_book price
  |> Option.value_map ~default:0 ~f:(fun level -> level.PriceLevel.total_qty)

let match_orders t =
  (* Simple matching logic - match best bid with best ask if they cross *)
  let rec match_loop t executions =
    match get_best_bid t, get_best_ask t with
    | Some (bid_price, _), Some (ask_price, _) when Float.(bid_price >= ask_price) ->
        (* Get the orders *)
        let bid_level = Map.find_exn t.bids bid_price in
        let ask_level = Map.find_exn t.asks ask_price in

        (match Queue.peek bid_level.orders, Queue.peek ask_level.orders with
        | Some buy_order, Some sell_order ->
            let exec_price = ask_price in (* Price improvement goes to taker *)
            let exec_qty = Int.min buy_order.remaining_qty sell_order.remaining_qty in

            let execution = Types.Execution.create
              ~buy_order_id:buy_order.id
              ~sell_order_id:sell_order.id
              ~price:exec_price
              ~quantity:exec_qty
            in

            (* Update orders *)
            let buy_order' = Types.Order.reduce_qty buy_order ~by:exec_qty in
            let sell_order' = Types.Order.reduce_qty sell_order ~by:exec_qty in

            (* Remove filled orders from queues *)
            let t' =
              if Types.Order.is_filled buy_order' then
                Option.value_exn (cancel_order t buy_order.id)
              else t
            in
            let t'' =
              if Types.Order.is_filled sell_order' then
                Option.value_exn (cancel_order t' sell_order.id)
              else t'
            in

            match_loop t'' (execution :: executions)
        | _ -> (List.rev executions, t))
    | _ -> (List.rev executions, t)
  in
  match_loop t []

let to_string t =
  let bid_str = get_bid_depth t 5
    |> List.map ~f:(fun (p, q) -> sprintf "%.2f(%d)" p q)
    |> String.concat ~sep:" | "
  in
  let ask_str = get_ask_depth t 5
    |> List.map ~f:(fun (p, q) -> sprintf "%.2f(%d)" p q)
    |> String.concat ~sep:" | "
  in
  sprintf "BIDS: %s || ASKS: %s" bid_str ask_str

module Stats = struct
  type stats = {
    total_orders: int;
    total_executions: int;
    total_volume: int;
    avg_spread: float;
  }

  let compute t =
    let total_orders = Hashtbl.length t.order_map in
    let total_executions = List.length t.executions in
    let total_volume =
      List.fold t.executions ~init:0 ~f:(fun acc exec ->
        acc + exec.Types.Execution.quantity
      )
    in
    let avg_spread = Option.value (get_spread t) ~default:0.0 in
    { total_orders; total_executions; total_volume; avg_spread }
end
