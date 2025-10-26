open Core
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

module ScheduledEvent = struct
  type 'a t = {
    event: 'a event;
    scheduled_time: Time_ns_unix.t;
  } [@@deriving sexp_of]

  let compare t1 t2 =
    Time_ns_unix.compare t1.scheduled_time t2.scheduled_time
end

type 'a t = {
  mutable event_queue: 'a ScheduledEvent.t list;
  mutable subscribers: ('a event -> unit Deferred.t) list;
  mutable running: bool;
}

let create () = {
  event_queue = [];
  subscribers = [];
  running = false;
}

let schedule t event ~at =
  let scheduled = { ScheduledEvent.event; scheduled_time = at } in
  t.event_queue <- List.sort ~compare:ScheduledEvent.compare (scheduled :: t.event_queue)

let subscribe t handler =
  t.subscribers <- handler :: t.subscribers

let stop t =
  t.running <- false

let run t ~until =
  t.running <- true;
  let rec loop () =
    if not t.running then
      return ()
    else
      match t.event_queue with
      | [] ->
          (* No more events *)
          return ()
      | scheduled :: rest ->
          if Time_ns_unix.(scheduled.ScheduledEvent.scheduled_time > until) then begin
            (* Event is beyond simulation time, stop *)
            return ()
          end else begin
            (* Process event *)
            t.event_queue <- rest;
            let%bind () =
              Deferred.List.iter t.subscribers ~how:`Sequential ~f:(fun handler ->
                handler scheduled.ScheduledEvent.event
              )
            in
            loop ()
          end
  in
  loop ()
