#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"

install_mongosh_if_missing() {
  if command -v mongosh >/dev/null 2>&1; then
    echo "mongosh is already installed: $(mongosh --version | head -n 1)"
    return 0
  fi

  echo "mongosh was not found. Trying to install mongodb-mongosh..."

  if ! command -v apt-get >/dev/null 2>&1; then
    echo "Automatic mongosh installation is supported here only for Debian/Ubuntu/WSL with apt-get."
    echo "Please install mongosh manually and re-run this script."
    exit 1
  fi

  if ! command -v sudo >/dev/null 2>&1; then
    echo "sudo is required to install mongosh automatically."
    exit 1
  fi

  local codename=""
  if command -v lsb_release >/dev/null 2>&1; then
    codename="$(lsb_release -cs)"
  elif [ -r /etc/os-release ]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    codename="${VERSION_CODENAME:-}"
  fi

  if [ -z "$codename" ]; then
    echo "Could not detect Ubuntu/Debian codename."
    echo "Please install mongosh manually and re-run this script."
    exit 1
  fi

  sudo apt-get update
  sudo apt-get install -y gnupg curl ca-certificates

  curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc \
    | sudo gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg \
    --dearmor --yes

  echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu ${codename}/mongodb-org/8.0 multiverse" \
    | sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list >/dev/null

  set +e
  sudo apt-get update
  local repo_status=$?
  set -e

  if [ "$repo_status" -ne 0 ]; then
    echo "MongoDB repo for '${codename}' did not work. Trying common WSL fallback: jammy..."
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/8.0 multiverse" \
      | sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list >/dev/null
    sudo apt-get update
  fi

  sudo apt-get install -y mongodb-mongosh

  if ! command -v mongosh >/dev/null 2>&1; then
    echo "mongosh installation finished, but mongosh is still not available in PATH."
    exit 1
  fi

  echo "mongosh installed: $(mongosh --version | head -n 1)"
}

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python 3 is required but was not found."
  exit 1
fi

install_mongosh_if_missing

if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment: $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip >/dev/null

set +e
python - <<'CHECKREQS'
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import sys

missing = []
for raw_line in Path("requirements.txt").read_text(encoding="utf-8").splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#"):
        continue
    package = line.split("==", 1)[0].strip()
    expected = line.split("==", 1)[1].strip() if "==" in line else None
    try:
        installed = version(package)
    except PackageNotFoundError:
        missing.append(line)
        continue
    if expected and installed != expected:
        missing.append(f"{line} (installed: {installed})")

if missing:
    print("Missing or incompatible packages:")
    for item in missing:
        print(" -", item)
    sys.exit(1)
print("Python packages are already installed and compatible.")
CHECKREQS
REQ_STATUS=$?
set -e

if [ "$REQ_STATUS" -ne 0 ]; then
  python -m pip install -r requirements.txt
fi

if [[ "${1:-}" == "--download-dataset" ]]; then
  python main.py --download-dataset
elif [[ "${1:-}" == "--run-all" ]]; then
  python main.py --download-dataset --all
else
  echo "Environment is ready."
  echo "Optional commands:"
  echo "  ./setup_project.sh --download-dataset"
  echo "  python main.py"
  echo "  python main.py --load --transform"
  echo "  python main.py --part2 --part3 --part4"
fi
