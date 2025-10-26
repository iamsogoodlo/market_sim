type t

val create : unit -> t

val add_order : t -> Types.Order.t -> t

val cancel_order : t -> Types.OrderId.t -> t option

val match_orders : t -> Types.Execution.t list * t

val get_bbo : t -> (float * float) option

val get_bid_depth : t -> int -> (float * int) list

val get_ask_depth : t -> int -> (float * int) list

val get_spread : t -> float option

val get_mid_price : t -> float option

val get_volume_at_price : t -> side:Types.Side.t -> price:float -> int

val to_string : t -> string

module Stats : sig
  type stats = {
    total_orders: int;
    total_executions: int;
    total_volume: int;
    avg_spread: float;
  }

  val compute : t -> stats
end
