#!/bin/bash
# Better WBW - Frontend Starter

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "--- Starting Frontend (Vite) ---"

if [ ! -d "frontend" ]; then
  echo "Error: frontend/ directory not found. Run this script from the project root."
  exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
  echo "Installing dependencies..."
  (cd frontend && npm install)
fi

cd frontend
echo "Running: npm run dev (stop with Ctrl+C)"
npm run dev
