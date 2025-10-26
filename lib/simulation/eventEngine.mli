open Async
open Core_types

[@@@warning "-33"]
open Core_unix

type 'a event =
  | MarketData of Types.MarketData.update
  | Fill of Types.Execution.t
  | RiskCheck of Types.Position.t
  | Timer of Time_ns_unix.t
  | Custom of 'a
[@@deriving sexp_of]

type 'a t

val create : unit -> 'a t

val schedule : 'a t -> 'a event -> at:Time_ns_unix.t -> unit

val subscribe : 'a t -> ('a event -> unit Deferred.t) -> unit

val run : 'a t -> until:Time_ns_unix.t -> unit Deferred.t

val stop : 'a t -> unit
