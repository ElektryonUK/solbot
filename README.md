# Solbot

High-Performance Solana Arbitrage Bot — Multi-DEX arbitrage across Jupiter, Raydium, Orca, Phoenix & Meteora with Jito MEV protection.

## Setup

### Environment Variables

```bash
# Core configuration
ENV=dev
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
USER_KEYPAIR=your_base58_private_key
USER_PUBKEY=your_wallet_address

# Jupiter API endpoints (2025 version)
JUP_QUOTE_BASE=https://api.jup.ag/swap/v1
JUP_SWAP_BASE=https://api.jup.ag/swap/v1

# Scanning parameters
SCAN_INTERVAL_MS=1000
PAUSE_AFTER_FAILS=5

# Risk management
MIN_PROFIT_USD=0.02
MAX_NOTIONAL_USD=0.50
MAX_DAILY_LOSS_USD=0.10

# Slippage tolerance
SLIPPAGE_BPS_PER_LEG=50
MAX_ROUTE_SLIPPAGE_BPS=100

# Priority fees
PRIORITY_FEE_MICRO_LAMPORTS=1500
TARGET_CU=1200000

# Execution modes
DRY_RUN=false
PAPER_TRADE=false

# Development/testing
OFFLINE_QUOTES=false
OFFLINE_DISCOVERY=true
```

## API Endpoints

**Updated for 2025 Jupiter API:**
- Quote endpoint: `https://api.jup.ag/swap/v1/quote`
- Swap endpoint: `https://api.jup.ag/swap/v1/swap`

**Migration Note:** If you see error: "No legs and no recognizable fields", ensure your `.env` contains the updated `JUP_QUOTE_BASE` and `JUP_SWAP_BASE` endpoints above.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Test with small position for 30 seconds
TIMEBOX_SECONDS=30 MAX_NOTIONAL_USD=0.25 ./scripts/start.sh
```

## Architecture

The bot follows the Jupiter Swap API flow:
1. **Discovery**: Find profitable arbitrage pairs
2. **Quote**: Get `routePlan` from Jupiter's quote endpoint
3. **Build**: Construct swap transaction with priority fees
4. **Sign**: Sign transaction locally with your keypair
5. **Execute**: Submit to Solana network

## Features

- Multi-DEX arbitrage detection
- Priority fee optimization
- Risk management and daily loss limits
- Dry-run and paper trading modes
- Jito MEV protection (when configured)
