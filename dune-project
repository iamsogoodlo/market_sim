(lang dune 3.12)
(name market_sim)
(version 0.1.0)

(generate_opam_files true)

(source (github yourusername/market_sim))
(license MIT)
(authors "Your Name")
(maintainers "your.email@example.com")

(package
 (name market_sim)
 (synopsis "Market Making Simulator")
 (description "A comprehensive market-making simulator with OCaml")
 (depends
  (ocaml (>= 5.0.0))
  dune
  (core (>= v0.16.0))
  (async (>= v0.16.0))
  (core_unix (>= v0.16.0))
  (ppx_jane (>= v0.16.0))
  (incremental (>= v0.16.0))
  (dream (>= 1.0.0~alpha5))
  (yojson (>= 2.0.0))
  (lwt (>= 5.6.0))
  (qcheck (and :with-test (>= 0.21)))
  (core_bench (and :with-test (>= v0.16.0)))))
