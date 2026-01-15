#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run with sudo." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEST_DIR="/opt/sensor_pi"
ENV_FILE="/etc/sensor_pi.env"
VENV_DIR="${DEST_DIR}/.venv"

echo "Installing Sensor Pi to ${DEST_DIR}..."
mkdir -p "${DEST_DIR}"
cp -a "${SRC_DIR}/." "${DEST_DIR}/"

if [[ -f "${DEST_DIR}/requirements.txt" ]]; then
  echo "Installing Python deps in ${VENV_DIR}..."
  /usr/bin/python3 -m venv "${VENV_DIR}"
  "${VENV_DIR}/bin/python" -m pip install --upgrade pip
  "${VENV_DIR}/bin/python" -m pip install -r "${DEST_DIR}/requirements.txt"
else
  echo "No requirements.txt found; skipping deps install."
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Creating ${ENV_FILE} from env.example..."
  cp "${SRC_DIR}/env.example" "${ENV_FILE}"
  chmod 600 "${ENV_FILE}"
else
  echo "Env file exists: ${ENV_FILE} (not overwritten)"
fi

echo "Installing systemd unit..."
cp "${SRC_DIR}/systemd/sensor-pi-publisher.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now sensor-pi-publisher

echo "Done."
