#!/usr/bin/env bash
set -euo pipefail

cargo build --locked -p shinobi-game-client --target wasm32-unknown-unknown --release

wasm-bindgen \
  --target web \
  --remove-name-section \
  --remove-producers-section \
  --out-dir dist/wasm \
  --out-name shinobi_game_client \
  dist/cargo-target/wasm32-unknown-unknown/release/shinobi_game_client.wasm
