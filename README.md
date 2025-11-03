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

# Jupiter Ultra API (authenticated, 5 RPS)
JUP_API_KEY=e7e6ab0e-1683-4226-a6da-760d05ebbf05
JUP_ORDER_BASE=https://api.jup.ag/ultra/v1
JUP_EXECUTE_BASE=https://api.jup.ag/ultra/v1

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

**Updated for Jupiter Ultra API (authenticated):**
- Order endpoint: `https://api.jup.ag/ultra/v1/order`
- Execute endpoint: `https://api.jup.ag/ultra/v1/execute`
- Authentication: `X-API-Key` header required

**Migration Note:** Jupiter Ultra API provides pre-built transactions, eliminating the need for complex routePlan parsing. The bot now follows: Order → Sign → Execute flow.

## Quick Start

```bash
# Add your API key to .env
echo "JUP_API_KEY=e7e6ab0e-1683-4226-a6da-760d05ebbf05" >> .env
echo "JUP_ORDER_BASE=https://api.jup.ag/ultra/v1" >> .env
echo "JUP_EXECUTE_BASE=https://api.jup.ag/ultra/v1" >> .env

# Install dependencies
pip install -r requirements.txt

# Test with small position for 30 seconds
TIMEBOX_SECONDS=30 MAX_NOTIONAL_USD=0.25 ./scripts/start.sh
```

## Architecture

The bot follows the Jupiter Ultra API flow:
1. **Discovery**: Find profitable arbitrage pairs
2. **Order**: Get pre-built transaction from Ultra `/order` endpoint
3. **Sign**: Sign transaction locally with your keypair
4. **Execute**: Submit signed transaction via Ultra `/execute` endpoint

## Features

- Multi-DEX arbitrage detection
- Priority fee optimization
- Risk management and daily loss limits
- Dry-run and paper trading modes
- Jito MEV protection (when configured)
- Rate limited to 5 RPS with provided API key
