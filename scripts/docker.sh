#!/usr/bin/env bash
set -euo pipefail

docker build -t solbot:latest .
docker run --rm -it --env-file .env -p 8080:8080 solbot:latest
