#!/usr/bin/env bash
set -e

echo "========================================="
echo "  Starting FlowPulse SaaS Platform       "
echo "========================================="

if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

if command -v docker >/dev/null 2>&1; then
    echo "Docker found. Launching via Docker Compose..."
    docker compose up --build
else
    echo "Docker not found in PATH."
fi
