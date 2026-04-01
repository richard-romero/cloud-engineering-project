#!/usr/bin/env bash
set -e

log() {
    echo "[BOOTSTRAP] $1"
}

log "Updating packages..."

sudo dnf update -y || sudo apt update -y

if ! command -v docker >/dev/null; then
    log "Installing Docker..."

    sudo dnf install -y docker || sudo apt install -y docker.io

    sudo systemctl enable docker
    sudo systemctl start docker
else
    log "Docker already installed"
fi

if ! sudo systemctl is-active --quiet docker; then
    log "Starting Docker..."
    sudo systemctl start docker
fi

sudo usermod -aG docker ec2-user || true

if command -v ufw >/dev/null; then
    sudo ufw allow 22
    sudo ufw allow 80
fi

IMAGE="nginx:latest"

log "Pulling container image..."
sudo docker pull "$IMAGE"

if sudo docker ps -a --format '{{.Names}}' | grep -q webapp; then
    log "Removing existing container..."
    sudo docker rm -f webapp
fi

log "Starting container..."

sudo docker run -d \
    --name webapp \
    -p 80:80 \
    --restart unless-stopped \
    "$IMAGE"

log "Bootstrap complete."
