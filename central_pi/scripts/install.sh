#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run with sudo." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEST_DIR="/opt/central_pi"
ENV_FILE="/etc/central_pi.env"
VENV_DIR="${DEST_DIR}/.venv"

echo "Installing Central Pi to ${DEST_DIR}..."
mkdir -p "${DEST_DIR}"
cp -a "${SRC_DIR}/." "${DEST_DIR}/"

echo "Installing Python deps in ${VENV_DIR}..."
/usr/bin/python3 -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/python" -m pip install --upgrade pip
"${VENV_DIR}/bin/python" -m pip install -r "${DEST_DIR}/requirements.txt"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Creating ${ENV_FILE} from env.example..."
  cp "${SRC_DIR}/env.example" "${ENV_FILE}"
  chmod 600 "${ENV_FILE}"
else
  echo "Env file exists: ${ENV_FILE} (not overwritten)"
fi

echo "Installing systemd units..."
cp "${SRC_DIR}/systemd/central-pi-api.service" /etc/systemd/system/
cp "${SRC_DIR}/systemd/central-pi-consumer.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now central-pi-api central-pi-consumer

echo "Done."
