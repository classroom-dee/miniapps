#!/usr/bin/env bash

set -eou pipefail

export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"
export PROJECT_DIR="$(pwd -P)"

COMPOSE_FILE="/lab/dee/repos_side/mini_apps/aider-ollama/docker-compose.yaml"

echo "PROJECT_DIR=$PROJECT_DIR"
echo "HOST_UID=$HOST_UID"
echo "HOST_GID=$HOST_GID"

docker compose -f "$COMPOSE_FILE" down