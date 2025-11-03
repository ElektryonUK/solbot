# Offline Mode

Set OFFLINE_DISCOVERY=true to skip external token discovery and use a built-in watchlist (USDC/SOL and USDT/SOL) to validate the bot loop without network DNS.

Steps:
- export OFFLINE_DISCOVERY=true
- ./scripts/dry_run.sh
