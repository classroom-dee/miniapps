#!/usr/bin/env bash

set -eou pipefail

export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"
export PROJECT_DIR="$(pwd -P)"

COMPOSE_FILE="/lab/dee/repos_side/mini_apps/aider-ollama/docker-compose.yaml"

echo "PROJECT_DIR=$PROJECT_DIR"
echo "HOST_UID=$HOST_UID"
echo "HOST_GID=$HOST_GID"

docker compose -f "$COMPOSE_FILE" up -d ollama

docker exec -it ollama nvidia-smi

docker exec -it ollama ollama pull qwen2.5-coder:14b

docker compose -f "$COMPOSE_FILE" run --rm aider \
  --model ollama/qwen2.5-coder:14b \
  /workspace