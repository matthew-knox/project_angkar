#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run with sudo." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEST_DIR="/opt/queue_pi"

echo "Installing Queue Pi to ${DEST_DIR}..."
mkdir -p "${DEST_DIR}"
cp -a "${SRC_DIR}/." "${DEST_DIR}/"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed. Please install Docker first." >&2
  exit 1
fi

if ! command -v docker-compose >/dev/null 2>&1; then
  if docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
  else
    echo "docker compose not available. Install docker-compose or the compose plugin." >&2
    exit 1
  fi
else
  DOCKER_COMPOSE="docker-compose"
fi

systemctl enable --now docker

echo "Starting services via Docker Compose..."
cd "${DEST_DIR}"
${DOCKER_COMPOSE} up -d --build

echo "Done."
