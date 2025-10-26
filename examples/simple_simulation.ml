open Core
open Async
open Core_types
open Strategies
open Simulation

(* Simple market simulation example *)

let create_market_maker () =
  let params = MarketMaker.AS_Params.{
    risk_aversion = 0.1;
    volatility = 0.02;
    terminal_time = Time_ns.Span.of_int_sec 3600;
    tick_size = 0.01;
  } in
  let strategy = MarketMaker.Strategy.AvellanedaStoikov params in
  Agent.create ~id:"market_maker_1" ~behavior:(Agent.Behavior.MarketMaker strategy)

let create_noise_traders n =
  List.init n ~f:(fun i ->
    Agent.create
      ~id:(sprintf "noise_%d" i)
      ~behavior:(Agent.Behavior.Noise {
        arrival_rate = 0.1;
        size_dist = (fun _ -> Random.int_incl 1 20);
      })
  )

let create_informed_traders n =
  List.init n ~f:(fun i ->
    let signal = Random.float_range (-1.0) 1.0 in
    Agent.create
      ~id:(sprintf "informed_%d" i)
      ~behavior:(Agent.Behavior.Informed {
        signal_strength = signal;
        trade_size = 10;
      })
  )

let print_orderbook ob =
  print_endline "\n=== Order Book ===";
  print_endline (OrderBook.to_string ob);
  (match OrderBook.get_bbo ob with
  | Some (bid, ask) ->
      printf "BBO: Bid=%.2f Ask=%.2f Spread=%.2f\n" bid ask (ask -. bid)
  | None ->
      print_endline "No BBO");
  (match OrderBook.get_mid_price ob with
  | Some mid -> printf "Mid Price: %.2f\n" mid
  | None -> ());
  print_endline "================\n"

let print_execution exec =
  printf "EXECUTION: Price=%.2f Qty=%d Time=%s\n"
    exec.Types.Execution.price
    exec.quantity
    (Time_ns_unix.to_string exec.timestamp)

let run_simulation () =
  let open Deferred.Let_syntax in

  (* Initialize *)
  let orderbook = ref (OrderBook.create ()) in
  let market_maker = create_market_maker () in
  let noise_traders = create_noise_traders 5 in
  let informed_traders = create_informed_traders 2 in
  let all_agents = market_maker :: (noise_traders @ informed_traders) in

  print_endline "Starting Market Simulation...";
  print_endline (sprintf "Agents: 1 MM, %d Noise, %d Informed"
    (List.length noise_traders)
    (List.length informed_traders));

  (* Simulation loop *)
  let rec simulation_step step =
    if step > 100 then
      return ()
    else begin
      (* Each agent decides action *)
      let market_data = match OrderBook.get_bbo !orderbook with
        | Some (bid_price, ask_price) ->
            Some {
              Types.MarketData.bid_price = Some bid_price;
              bid_size = OrderBook.get_volume_at_price !orderbook ~side:Buy ~price:bid_price;
              ask_price = Some ask_price;
              ask_size = OrderBook.get_volume_at_price !orderbook ~side:Sell ~price:ask_price;
              timestamp = Time_ns_unix.now ();
            }
        | None -> None
      in

      (* Collect orders from all agents *)
      let new_orders =
        List.concat_map all_agents ~f:(fun agent ->
          Agent.decide_action agent ~orderbook:!orderbook ~market_data
        )
      in

      (* Add orders to book *)
      orderbook := List.fold new_orders ~init:!orderbook ~f:(fun ob order ->
        OrderBook.add_order ob order
      );

      (* Match orders *)
      let executions, new_ob = OrderBook.match_orders !orderbook in
      orderbook := new_ob;

      (* Print executions *)
      List.iter executions ~f:print_execution;

      (* Update agent positions *)
      List.iter executions ~f:(fun exec ->
        List.iter all_agents ~f:(fun agent ->
          (* Update both buyer and seller *)
          if List.exists agent.active_orders ~f:(fun oid ->
            Types.OrderId.equal oid exec.buy_order_id) then
            Agent.update_position agent ~execution:exec ~side:Buy;
          if List.exists agent.active_orders ~f:(fun oid ->
            Types.OrderId.equal oid exec.sell_order_id) then
            Agent.update_position agent ~execution:exec ~side:Sell;
        )
      );

      (* Print status every 10 steps *)
      if step % 10 = 0 then begin
        printf "\n--- Step %d ---\n" step;
        print_orderbook !orderbook;
        printf "Market Maker Position: %d\n" market_maker.position.quantity;
        printf "Market Maker P&L: %.2f\n"
          (match OrderBook.get_mid_price !orderbook with
          | Some mid -> Types.Position.total_pnl market_maker.position ~mark_price:mid
          | None -> 0.0);
      end;

      (* Small delay *)
      let%bind () = after (Time_float.Span.of_ms 100.0) in
      simulation_step (step + 1)
    end
  in

  simulation_step 0

let () =
  Command.async ~summary:"Run a simple market simulation"
    Command.Let_syntax.(
      let%map_open () = return () in
      fun () -> run_simulation ()
    )
  |> Command_unix.run
