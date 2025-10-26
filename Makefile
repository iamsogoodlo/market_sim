.PHONY: build test clean install run server

build:
	dune build

test:
	dune test

clean:
	dune clean

install:
	opam install . --deps-only

run:
	dune exec market_sim_server

server: build
	dune exec market_sim_server

watch:
	dune build --watch

fmt:
	dune build @fmt --auto-promote

doc:
	dune build @doc

bench:
	dune exec test/test_market_sim.exe -- -bench
