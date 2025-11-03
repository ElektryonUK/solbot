# Solbot — Setup & Run Guide

This document describes how to set up, configure, and run Solbot using the latest LTS technologies as of Nov 2025.

## 1) Prerequisites
- OS: Ubuntu 22.04/24.04 LTS or macOS 14+
- Python: 3.11 LTS
- Docker: 26.x LTS (optional, for containerized run)
- Git

## 2) Clone & Configure

```
git clone https://github.com/ElektryonUK/solbot.git
cd solbot
cp .env.example .env
# edit .env with your values
```

.env example variables:
```
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
JITO_RPC_URL=https://mainnet.block-engine.jito.wtf/api/v1/bundles
USER_PUBKEY=<YOUR_PUBLIC_KEY>
USER_KEYPAIR=<BASE58_OR_JSON_KEYPAIR>
ENV=prod
```

## 3) Local (venv)
```
./scripts/bootstrap.sh
./scripts/dev.sh
```
API will run at http://localhost:8080/healthz

## 4) Docker
```
./scripts/docker.sh
```

## 5) Production Notes
- Use a private RPC with high TPS and low latency
- Prefer Jito bundles for execution protection
- Securely load keypairs (KMS or env-injected secrets)
- Run with process manager (systemd or docker-compose)

## 6) Testing
```
pytest -q
```
