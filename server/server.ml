open Lwt.Syntax
open Core
open Core_types

(* Global order book state *)
let orderbook = ref (OrderBook.create ())

(* Broadcast channel for order updates *)
let subscribers : (string -> unit Lwt.t) list ref = ref []

let broadcast_message msg =
  Lwt_list.iter_p (fun send -> send msg) !subscribers

let handle_order_message msg =
  try
    Dream.log "Processing message: %s" msg;
    let json = Yojson.Basic.from_string msg in
    let open Yojson.Basic.Util in
    let action = json |> member "action" |> to_string in

    match action with
    | "place_order" ->
        Dream.log "Placing order...";
        let side_str = json |> member "side" |> to_string in
        let order_type_str = json |> member "orderType" |> to_string in
        let price =
          try json |> member "price" |> to_float
          with _ -> json |> member "price" |> to_int |> Float.of_int in
        let quantity = json |> member "quantity" |> to_int in
        let trader_id = json |> member "traderId" |> to_string_option
                        |> Option.value ~default:"WebUser" in
        let symbol = json |> member "symbol" |> to_string_option
                     |> Option.value ~default:"AAPL" in

        Dream.log "Order details: side=%s type=%s price=%.2f qty=%d trader=%s symbol=%s"
          side_str order_type_str price quantity trader_id symbol;

        let side = match side_str with
          | "buy" -> Types.Side.Buy
          | "sell" -> Types.Side.Sell
          | _ -> Types.Side.Buy
        in

        let order_type = match order_type_str with
          | "market" -> Types.OrderType.Market
          | "limit" -> Types.OrderType.Limit { price }
          | _ -> Types.OrderType.Limit { price }
        in

        let order = Types.Order.create ~side ~order_type ~quantity ~trader_id ~symbol () in
        Dream.log "Order created with ID: %s" (Types.OrderId.to_string order.id);

        (* Save order to database *)
        let%lwt () = Db.save_order order in
        Dream.log "Order saved to database";

        orderbook := OrderBook.add_order !orderbook order;
        Dream.log "Order added to book";

        (* Try to match orders *)
        let executions, new_ob = OrderBook.match_orders !orderbook in
        orderbook := new_ob;
        Dream.log "Matching complete. Executions: %d" (List.length executions);

        (* Save executions to database *)
        let%lwt () = Lwt_list.iter_s Db.save_execution executions in
        Dream.log "Executions saved to database";

        (* Broadcast order to all clients *)
        let order_id_str = Types.OrderId.to_string order.id in
        let order_msg = Printf.sprintf
          {|{"type":"order","side":"%s","price":%.2f,"quantity":%d,"trader":"%s","orderId":"%s","symbol":"%s"}|}
          side_str price quantity trader_id order_id_str symbol in
        Dream.log "Broadcasting order: %s" order_msg;
        let%lwt () = broadcast_message order_msg in
        Dream.log "Order broadcast complete";

        (* Broadcast executions *)
        let%lwt () = Lwt_list.iter_s (fun exec ->
          let exec_msg = Printf.sprintf
            {|{"type":"execution","price":%.2f,"quantity":%d}|}
            exec.Types.Execution.price exec.quantity in
          Dream.log "Broadcasting execution: %s" exec_msg;
          broadcast_message exec_msg
        ) executions in

        (* Send order book snapshot *)
        let bbo = OrderBook.get_bbo !orderbook in
        let spread = OrderBook.get_spread !orderbook in
        let snapshot = Printf.sprintf
          {|{"type":"snapshot","bbo":%s,"spread":%s}|}
          (match bbo with
           | Some (bid, ask) -> Printf.sprintf {|{"bid":%.2f,"ask":%.2f}|} bid ask
           | None -> "null")
          (match spread with
           | Some s -> Printf.sprintf "%.2f" s
           | None -> "null") in
        Dream.log "Broadcasting snapshot: %s" snapshot;
        broadcast_message snapshot

    | _ ->
        Dream.log "Unknown action: %s" action;
        Lwt.return_unit
  with
  | e ->
      Dream.log "Error handling message: %s" (Exn.to_string e);
      Lwt.return_unit

let websocket_handler = fun _request ->
  Dream.websocket (fun websocket ->
    let send_msg msg = Dream.send websocket msg in
    subscribers := send_msg :: !subscribers;

    let* () = Dream.send websocket {|{"type":"connected"}|} in

    (* Send initial order book state *)
    let bbo = OrderBook.get_bbo !orderbook in
    let spread = OrderBook.get_spread !orderbook in
    let bid_depth = OrderBook.get_bid_depth !orderbook 10 in
    let ask_depth = OrderBook.get_ask_depth !orderbook 10 in

    Dream.log "Sending initial state - Bid depth: %d levels, Ask depth: %d levels"
      (List.length bid_depth) (List.length ask_depth);

    let snapshot = Printf.sprintf
      {|{"type":"snapshot","bbo":%s,"spread":%s}|}
      (match bbo with
       | Some (bid, ask) -> Printf.sprintf {|{"bid":%.2f,"ask":%.2f}|} bid ask
       | None -> "null")
      (match spread with
       | Some s -> Printf.sprintf "%.2f" s
       | None -> "null") in
    let* () = Dream.send websocket snapshot in

    (* Send bid depth as orders *)
    let* () = Lwt_list.iter_s (fun (price, qty) ->
      let order_msg = Printf.sprintf
        {|{"type":"order","side":"buy","price":%.2f,"quantity":%d,"trader":"System","orderId":"depth"}|}
        price qty in
      Dream.log "Sending bid depth: price=%.2f qty=%d" price qty;
      Dream.send websocket order_msg
    ) bid_depth in

    (* Send ask depth as orders *)
    let* () = Lwt_list.iter_s (fun (price, qty) ->
      let order_msg = Printf.sprintf
        {|{"type":"order","side":"sell","price":%.2f,"quantity":%d,"trader":"System","orderId":"depth"}|}
        price qty in
      Dream.log "Sending ask depth: price=%.2f qty=%d" price qty;
      Dream.send websocket order_msg
    ) ask_depth in

    let rec loop () =
      let* msg_opt = Dream.receive websocket in
      match msg_opt with
      | Some msg ->
          Dream.log "Received: %s" msg;
          let%lwt () = handle_order_message msg in
          loop ()
      | None ->
          Dream.log "WebSocket closed";
          subscribers := List.filter ~f:(fun s -> not (phys_equal s send_msg)) !subscribers;
          Lwt.return_unit
    in
    loop ())

let index_handler _request =
  Dream.html
    {|
<!DOCTYPE html>
<html>
<head>
  <title>Market Simulator - Live Trading</title>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
      background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
      color: #e0e0e0;
      min-height: 100vh;
      padding: 20px;
    }

    .container {
      max-width: 1600px;
      margin: 0 auto;
    }

    header {
      text-align: center;
      margin-bottom: 30px;
      padding: 20px;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 15px;
      backdrop-filter: blur(10px);
    }

    h1 {
      color: #00d4ff;
      font-size: 2.5em;
      text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
      margin-bottom: 10px;
    }

    .stats-bar {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 15px;
      margin-bottom: 20px;
    }

    .stat-card {
      background: rgba(255, 255, 255, 0.05);
      padding: 15px;
      border-radius: 10px;
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .stat-label {
      font-size: 0.8em;
      color: #888;
      text-transform: uppercase;
      letter-spacing: 1px;
    }

    .stat-value {
      font-size: 1.8em;
      font-weight: bold;
      margin-top: 5px;
    }

    .stat-value.green { color: #00ff88; }
    .stat-value.red { color: #ff4444; }
    .stat-value.blue { color: #00d4ff; }

    .main-grid {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 20px;
      margin-bottom: 20px;
    }

    .panel {
      background: rgba(255, 255, 255, 0.05);
      border-radius: 15px;
      padding: 20px;
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15px;
      padding-bottom: 10px;
      border-bottom: 2px solid rgba(255, 255, 255, 0.1);
    }

    .panel-title {
      font-size: 1.2em;
      font-weight: bold;
      color: #00d4ff;
    }

    .badge {
      padding: 4px 10px;
      border-radius: 12px;
      font-size: 0.75em;
      font-weight: bold;
    }

    .badge.connected {
      background: #00ff88;
      color: #000;
    }

    .badge.disconnected {
      background: #ff4444;
      color: #fff;
    }

    /* Order Book Styles */
    .orderbook-container {
      grid-column: span 2;
    }

    .orderbook-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 15px;
    }

    .orderbook-side {
      background: rgba(0, 0, 0, 0.2);
      padding: 15px;
      border-radius: 10px;
    }

    .orderbook-side.bids {
      border-left: 3px solid #00ff88;
    }

    .orderbook-side.asks {
      border-left: 3px solid #ff4444;
    }

    .orderbook-side h4 {
      color: #fff;
      margin-bottom: 10px;
      font-size: 1em;
    }

    .order-level {
      display: grid;
      grid-template-columns: 2fr 1fr 1fr;
      gap: 10px;
      padding: 8px;
      margin-bottom: 5px;
      background: rgba(255, 255, 255, 0.03);
      border-radius: 5px;
      font-size: 0.9em;
      transition: all 0.3s ease;
    }

    .order-level:hover {
      background: rgba(255, 255, 255, 0.08);
      transform: translateX(5px);
    }

    .order-level.bid .price { color: #00ff88; }
    .order-level.ask .price { color: #ff4444; }

    .order-level .price {
      font-weight: bold;
      font-size: 1.1em;
    }

    .order-level .size {
      color: #aaa;
    }

    /* Order Feed Styles */
    .order-feed-container {
      max-height: 600px;
      overflow-y: auto;
    }

    .order-feed-container::-webkit-scrollbar {
      width: 8px;
    }

    .order-feed-container::-webkit-scrollbar-track {
      background: rgba(255, 255, 255, 0.05);
      border-radius: 10px;
    }

    .order-feed-container::-webkit-scrollbar-thumb {
      background: rgba(0, 212, 255, 0.5);
      border-radius: 10px;
    }

    .order-item {
      padding: 12px;
      margin-bottom: 8px;
      background: rgba(255, 255, 255, 0.03);
      border-radius: 8px;
      border-left: 3px solid #00d4ff;
      animation: slideIn 0.3s ease;
      transition: all 0.2s ease;
    }

    .order-item:hover {
      background: rgba(255, 255, 255, 0.08);
      transform: translateX(5px);
    }

    .order-item.buy {
      border-left-color: #00ff88;
    }

    .order-item.sell {
      border-left-color: #ff4444;
    }

    .order-item.execution {
      border-left-color: #ffd700;
      background: rgba(255, 215, 0, 0.1);
    }

    @keyframes slideIn {
      from {
        opacity: 0;
        transform: translateX(-20px);
      }
      to {
        opacity: 1;
        transform: translateX(0);
      }
    }

    .order-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 5px;
    }

    .order-type {
      font-weight: bold;
      font-size: 0.9em;
      padding: 2px 8px;
      border-radius: 4px;
      text-transform: uppercase;
    }

    .order-type.buy {
      background: rgba(0, 255, 136, 0.2);
      color: #00ff88;
    }

    .order-type.sell {
      background: rgba(255, 68, 68, 0.2);
      color: #ff4444;
    }

    .order-type.execution {
      background: rgba(255, 215, 0, 0.2);
      color: #ffd700;
    }

    .order-time {
      font-size: 0.8em;
      color: #888;
    }

    .order-details {
      font-size: 0.9em;
      color: #ccc;
    }

    .order-price {
      font-weight: bold;
      font-size: 1.1em;
    }

    .order-price.buy { color: #00ff88; }
    .order-price.sell { color: #ff4444; }
    .order-price.execution { color: #ffd700; }

    .spread-indicator {
      text-align: center;
      padding: 10px;
      margin: 10px 0;
      background: rgba(255, 215, 0, 0.1);
      border-radius: 8px;
      border: 1px solid rgba(255, 215, 0, 0.3);
    }

    .spread-value {
      font-size: 1.2em;
      font-weight: bold;
      color: #ffd700;
    }

    .empty-state {
      text-align: center;
      padding: 40px;
      color: #666;
      font-style: italic;
    }

    /* Trading Form Styles */
    .trading-form {
      background: rgba(0, 0, 0, 0.3);
      padding: 20px;
      border-radius: 10px;
      margin-bottom: 20px;
    }

    .form-group {
      margin-bottom: 15px;
    }

    .form-group label {
      display: block;
      margin-bottom: 5px;
      color: #aaa;
      font-size: 0.9em;
      text-transform: uppercase;
      letter-spacing: 1px;
    }

    .form-group input,
    .form-group select {
      width: 100%;
      padding: 10px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 5px;
      color: #fff;
      font-family: inherit;
      font-size: 1em;
    }

    .form-group input:focus,
    .form-group select:focus {
      outline: none;
      border-color: #00d4ff;
      background: rgba(255, 255, 255, 0.08);
    }

    .button-group {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-top: 20px;
    }

    .btn {
      padding: 12px 20px;
      border: none;
      border-radius: 8px;
      font-family: inherit;
      font-size: 1em;
      font-weight: bold;
      cursor: pointer;
      transition: all 0.2s ease;
      text-transform: uppercase;
      letter-spacing: 1px;
    }

    .btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
    }

    .btn:active {
      transform: translateY(0);
    }

    .btn-buy {
      background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%);
      color: #000;
    }

    .btn-buy:hover {
      background: linear-gradient(135deg, #00ff88 0%, #00ff88 100%);
      box-shadow: 0 5px 20px rgba(0, 255, 136, 0.4);
    }

    .btn-sell {
      background: linear-gradient(135deg, #ff4444 0%, #cc0000 100%);
      color: #fff;
    }

    .btn-sell:hover {
      background: linear-gradient(135deg, #ff6666 0%, #ff4444 100%);
      box-shadow: 0 5px 20px rgba(255, 68, 68, 0.4);
    }

    .quick-prices {
      display: flex;
      gap: 5px;
      margin-top: 5px;
    }

    .quick-price-btn {
      padding: 5px 10px;
      background: rgba(0, 212, 255, 0.1);
      border: 1px solid rgba(0, 212, 255, 0.3);
      border-radius: 4px;
      color: #00d4ff;
      font-size: 0.85em;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .quick-price-btn:hover {
      background: rgba(0, 212, 255, 0.2);
      border-color: #00d4ff;
    }

    /* Responsive */
    @media (max-width: 1200px) {
      .main-grid {
        grid-template-columns: 1fr;
      }

      .orderbook-container {
        grid-column: span 1;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>🚀 Market Simulator</h1>
      <div class="stat-label">Real-Time Order Book & Trading Feed</div>
    </header>

    <div class="stats-bar">
      <div class="stat-card">
        <div class="stat-label">Connection</div>
        <div class="stat-value blue" id="connection-status">
          <span class="badge disconnected">Connecting...</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Orders</div>
        <div class="stat-value blue" id="total-orders">0</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Executions</div>
        <div class="stat-value" id="executions" style="color: #ffd700;">0</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Spread</div>
        <div class="stat-value" id="spread" style="color: #ffd700;">--</div>
      </div>
    </div>

    <div class="main-grid">
      <!-- Order Book -->
      <div class="panel orderbook-container">
        <div class="panel-header">
          <div class="panel-title">📊 Order Book</div>
        </div>
        <div class="orderbook-grid">
          <div class="orderbook-side bids">
            <h4>🟢 BIDS</h4>
            <div id="bids-list">
              <div class="empty-state">Waiting for orders...</div>
            </div>
          </div>
          <div class="orderbook-side asks">
            <h4>🔴 ASKS</h4>
            <div id="asks-list">
              <div class="empty-state">Waiting for orders...</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Live Order Feed -->
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">📈 Live Order Feed</div>
          <button onclick="clearFeed()" style="background: rgba(255,68,68,0.2); color: #ff4444; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer; font-family: inherit;">Clear</button>
        </div>
        <div class="order-feed-container" id="order-feed">
          <div class="empty-state">Waiting for orders...</div>
        </div>
      </div>
    </div>

    <!-- Trading Panel -->
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">💹 Place Order</div>
      </div>
      <form class="trading-form" id="orderForm" onsubmit="return placeOrder(event)">
        <div class="form-group">
          <label for="orderType">Order Type</label>
          <select id="orderType" name="orderType" onchange="togglePriceInput()">
            <option value="limit">Limit Order</option>
            <option value="market">Market Order</option>
          </select>
        </div>

        <div class="form-group" id="priceGroup">
          <label for="price">Price ($)</label>
          <input type="number" id="price" name="price" step="0.01" min="0" value="100.00" required>
          <div class="quick-prices">
            <button type="button" class="quick-price-btn" onclick="setPrice(95)">$95</button>
            <button type="button" class="quick-price-btn" onclick="setPrice(100)">$100</button>
            <button type="button" class="quick-price-btn" onclick="setPrice(105)">$105</button>
            <button type="button" class="quick-price-btn" onclick="setPrice(110)">$110</button>
          </div>
        </div>

        <div class="form-group">
          <label for="quantity">Quantity</label>
          <input type="number" id="quantity" name="quantity" min="1" value="10" required>
          <div class="quick-prices">
            <button type="button" class="quick-price-btn" onclick="setQuantity(10)">10</button>
            <button type="button" class="quick-price-btn" onclick="setQuantity(50)">50</button>
            <button type="button" class="quick-price-btn" onclick="setQuantity(100)">100</button>
            <button type="button" class="quick-price-btn" onclick="setQuantity(500)">500</button>
          </div>
        </div>

        <div class="form-group">
          <label for="traderId">Trader ID (optional)</label>
          <input type="text" id="traderId" name="traderId" placeholder="WebUser">
        </div>

        <div class="button-group">
          <button type="submit" name="side" value="buy" class="btn btn-buy" onclick="setSide('buy')">
            🟢 Buy
          </button>
          <button type="submit" name="side" value="sell" class="btn btn-sell" onclick="setSide('sell')">
            🔴 Sell
          </button>
        </div>
      </form>
    </div>
  </div>

  <script>
    let ws;
    let orderCount = 0;
    let executionCount = 0;
    let orders = [];

    function connect() {
      ws = new WebSocket('ws://localhost:8080/ws');
      const statusBadge = document.getElementById('connection-status');

      ws.onopen = () => {
        statusBadge.innerHTML = '<span class="badge connected">Connected</span>';
        console.log('Connected to server');

        // Send a message to start simulation
        ws.send(JSON.stringify({ action: 'start' }));
      };

      ws.onmessage = (event) => {
        console.log('Received:', event.data);
        handleMessage(event.data);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        statusBadge.innerHTML = '<span class="badge disconnected">Error</span>';
      };

      ws.onclose = () => {
        statusBadge.innerHTML = '<span class="badge disconnected">Disconnected</span>';
        console.log('Disconnected. Reconnecting...');
        setTimeout(connect, 2000);
      };
    }

    function handleMessage(data) {
      try {
        console.log('Raw message received:', data);
        const msg = JSON.parse(data);
        console.log('Parsed message:', msg);

        if (msg.type === 'order') {
          console.log('Processing order:', msg);
          const order = {
            type: msg.side,
            price: parseFloat(msg.price).toFixed(2),
            size: msg.quantity,
            time: new Date().toLocaleTimeString(),
            trader: msg.trader
          };
          console.log('Created order object:', order);
          addOrderToFeed(order);
          updateOrderBook(order);
          updateStats();
        } else if (msg.type === 'execution') {
          console.log('Processing execution:', msg);
          const exec = {
            type: 'execution',
            price: parseFloat(msg.price).toFixed(2),
            size: msg.quantity,
            time: new Date().toLocaleTimeString(),
            trader: 'MATCHED'
          };
          addOrderToFeed(exec);
          updateStats();
        } else if (msg.type === 'snapshot') {
          console.log('Processing snapshot:', msg);
          if (msg.bbo) {
            // Update spread display
            if (msg.spread) {
              document.getElementById('spread').textContent = `$${parseFloat(msg.spread).toFixed(2)}`;
            }
          }
        } else if (msg.type === 'connected') {
          console.log('Connected message received');
        } else {
          console.log('Unknown message type:', msg.type);
        }
      } catch (e) {
        console.error('Error parsing message:', e, 'Data:', data);
      }
    }

    function addOrderToFeed(order) {
      const feed = document.getElementById('order-feed');

      // Remove empty state
      if (feed.querySelector('.empty-state')) {
        feed.innerHTML = '';
      }

      const orderDiv = document.createElement('div');
      orderDiv.className = `order-item ${order.type}`;
      orderDiv.innerHTML = `
        <div class="order-header">
          <span class="order-type ${order.type}">${order.type === 'execution' ? '⚡ EXECUTION' : (order.type === 'buy' ? '🟢 BUY' : '🔴 SELL')}</span>
          <span class="order-time">${order.time}</span>
        </div>
        <div class="order-details">
          <span class="order-price ${order.type}">$${order.price}</span>
          <span style="color: #888;"> × </span>
          <span style="color: #aaa;">${order.size}</span>
          <span style="color: #666;"> | Trader: ${order.trader}</span>
        </div>
      `;

      feed.insertBefore(orderDiv, feed.firstChild);

      // Keep only last 50 orders
      while (feed.children.length > 50) {
        feed.removeChild(feed.lastChild);
      }

      orders.unshift(order);
      if (orders.length > 50) orders.pop();
    }

    function updateOrderBook(order) {
      // Simplified order book update
      const bidsList = document.getElementById('bids-list');
      const asksList = document.getElementById('asks-list');

      if (order.type === 'buy') {
        if (bidsList.querySelector('.empty-state')) {
          bidsList.innerHTML = '';
        }
        const levelDiv = document.createElement('div');
        levelDiv.className = 'order-level bid';
        levelDiv.innerHTML = `
          <span class="price">$${order.price}</span>
          <span class="size">${order.size}</span>
          <span class="trader">${order.trader}</span>
        `;
        bidsList.insertBefore(levelDiv, bidsList.firstChild);
        if (bidsList.children.length > 10) bidsList.removeChild(bidsList.lastChild);
      } else if (order.type === 'sell') {
        if (asksList.querySelector('.empty-state')) {
          asksList.innerHTML = '';
        }
        const levelDiv = document.createElement('div');
        levelDiv.className = 'order-level ask';
        levelDiv.innerHTML = `
          <span class="price">$${order.price}</span>
          <span class="size">${order.size}</span>
          <span class="trader">${order.trader}</span>
        `;
        asksList.appendChild(levelDiv);
        if (asksList.children.length > 10) asksList.removeChild(asksList.firstChild);
      }
    }

    function updateStats() {
      orderCount++;
      if (orders[0] && orders[0].type === 'execution') {
        executionCount++;
      }

      document.getElementById('total-orders').textContent = orderCount;
      document.getElementById('executions').textContent = executionCount;

      // Calculate spread
      const bidsList = document.getElementById('bids-list');
      const asksList = document.getElementById('asks-list');

      const highestBid = bidsList.querySelector('.order-level.bid .price');
      const lowestAsk = asksList.querySelector('.order-level.ask .price');

      if (highestBid && lowestAsk) {
        const bid = parseFloat(highestBid.textContent.replace('$', ''));
        const ask = parseFloat(lowestAsk.textContent.replace('$', ''));
        const spread = (ask - bid).toFixed(2);
        document.getElementById('spread').textContent = `$${spread}`;
      }
    }

    function clearFeed() {
      document.getElementById('order-feed').innerHTML = '<div class="empty-state">Feed cleared. Waiting for new orders...</div>';
      orders = [];
    }

    // Form handling
    let currentSide = 'buy';

    function setSide(side) {
      currentSide = side;
    }

    function togglePriceInput() {
      const orderType = document.getElementById('orderType').value;
      const priceGroup = document.getElementById('priceGroup');
      if (orderType === 'market') {
        priceGroup.style.display = 'none';
      } else {
        priceGroup.style.display = 'block';
      }
    }

    function setPrice(price) {
      document.getElementById('price').value = price.toFixed(2);
    }

    function setQuantity(qty) {
      document.getElementById('quantity').value = qty;
    }

    function placeOrder(event) {
      event.preventDefault();

      if (!ws || ws.readyState !== WebSocket.OPEN) {
        alert('Not connected to server. Please wait...');
        return false;
      }

      const form = document.getElementById('orderForm');
      const formData = new FormData(form);

      const orderType = formData.get('orderType');
      const price = parseFloat(formData.get('price')) || 100.0;
      const quantity = parseInt(formData.get('quantity'));
      const traderId = formData.get('traderId') || 'WebUser';

      const orderMessage = {
        action: 'place_order',
        side: currentSide,
        orderType: orderType,
        price: price,
        quantity: quantity,
        traderId: traderId
      };

      console.log('Sending order:', orderMessage);
      ws.send(JSON.stringify(orderMessage));

      // Visual feedback
      const btn = event.submitter;
      const originalText = btn.innerHTML;
      btn.innerHTML = '✓ Sent!';
      btn.disabled = true;

      setTimeout(() => {
        btn.innerHTML = originalText;
        btn.disabled = false;
      }, 1000);

      return false;
    }

    // Connect on load
    connect();
  </script>
</body>
</html>
    |}

let () =
  (* Load orders from database on startup *)
  let () =
    Lwt_main.run (
      let%lwt orders = Db.load_active_orders () in
      Dream.log "Loaded %d orders from database" (List.length orders);
      List.iter ~f:(fun order ->
        orderbook := OrderBook.add_order !orderbook order
      ) orders;
      Lwt.return_unit
    )
  in

  Dream.run ~port:8080
  @@ Dream.logger
  @@ Dream.router [
    Dream.get "/" index_handler;
    Dream.get "/app" (fun _request ->
      Dream.html (In_channel.read_all "server/brokerage_ui.html"));
    Dream.get "/api/stocks/list" (fun _request ->
      let output = Core_unix.open_process_in "python3 server/stock_data.py list 50" in
      let result = In_channel.input_all output in
      let _ = Core_unix.close_process_in output in
      Dream.json result);
    Dream.get "/api/stocks/search/:query" (fun request ->
      let query = Dream.param request "query" in
      let cmd = Printf.sprintf "python3 server/stock_data.py search '%s'" query in
      let output = Core_unix.open_process_in cmd in
      let result = In_channel.input_all output in
      let _ = Core_unix.close_process_in output in
      Dream.json result);
    Dream.get "/api/stocks/quote/:symbol" (fun request ->
      let symbol = Dream.param request "symbol" in
      let cmd = Printf.sprintf "python3 server/stock_data.py quote %s" symbol in
      let output = Core_unix.open_process_in cmd in
      let result = In_channel.input_all output in
      let _ = Core_unix.close_process_in output in
      Dream.json result);
    Dream.get "/api/stocks/historical/:symbol/:period" (fun request ->
      let symbol = Dream.param request "symbol" in
      let period = Dream.param request "period" in
      let cmd = Printf.sprintf "python3 server/stock_data.py historical %s %s" symbol period in
      let output = Core_unix.open_process_in cmd in
      let result = In_channel.input_all output in
      let _ = Core_unix.close_process_in output in
      Dream.json result);
    Dream.get "/ws" websocket_handler;
  ]
