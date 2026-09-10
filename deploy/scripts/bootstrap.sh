#!/usr/bin/env bash
set -euo pipefail

# Bootstrap Arena stack on the EC2 host (Amazon Linux 2023 or Ubuntu).
# Run from the repository root or set REPO_ROOT.

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
DEPLOY_DIR="${REPO_ROOT}/deploy"

echo "==> Repo root: ${REPO_ROOT}"

if ! command -v docker >/dev/null 2>&1; then
  echo "==> Installing Docker..."
  if command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y docker
    sudo systemctl enable --now docker
    sudo mkdir -p /usr/local/lib/docker/cli-plugins
    sudo curl -fsSL https://github.com/docker/compose/releases/download/v2.32.4/docker-compose-linux-x86_64 \
      -o /usr/local/lib/docker/cli-plugins/docker-compose
    sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
  else
    sudo apt-get update -y
    sudo apt-get install -y ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "${VERSION_CODENAME}") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  fi
  sudo usermod -aG docker "${USER}" || true
fi

if [[ ! -f "${DEPLOY_DIR}/.env" ]]; then
  echo "Missing ${DEPLOY_DIR}/.env — copy .env.example and fill secrets first."
  exit 1
fi

cd "${DEPLOY_DIR}"
echo "==> Building and starting compose stack..."
sudo docker compose up -d --build

echo "==> Stack status:"
sudo docker compose ps
echo "Bootstrap complete. Ensure GitHub OAuth redirect matches DOMAIN_NAME."
