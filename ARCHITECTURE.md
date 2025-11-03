# Architecture Overview

This bot comprises modular services for discovery, quoting, strategy generation, and execution. It supports:
- Multi-RPC pool with health probing
- Jupiter V6 quotes and transaction builds
- Optional Jito bundle submission for MEV protection
- Configurable risk and fees via environment

Execution Flow:
1. Discovery builds a watchlist of tradable pairs.
2. Strategies propose Plans ranked by expected PnL (net of slippage + priority fees).
3. Executor builds a swap tx (Jupiter), prepends compute budget ixs, and submits via RPC or Jito.
4. Confirmation and telemetry emitted to logs.
