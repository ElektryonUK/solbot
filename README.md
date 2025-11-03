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

# Jupiter API endpoints (public v6)
JUP_QUOTE_BASE=https://quote-api.jup.ag/v6
JUP_SWAP_BASE=https://quote-api.jup.ag/v6

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

**Updated for Jupiter API (public v6):**
- Quote endpoint: `https://quote-api.jup.ag/v6/quote`
- Swap endpoint: `https://quote-api.jup.ag/v6/swap`

**Migration Note:** If you see error: "400 Bad Request" on /swap, enable swap.response body logging (already added) and ensure `quoteResponse` is the full JSON returned by `/v6/quote` with a non-empty `routePlan`.
