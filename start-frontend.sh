#!/bin/bash
# Better WBW - Frontend Starter

echo "--- Starting Frontend (Vite) ---"

mkdir -p logs
cd frontend
npm run dev > ../logs/frontend_$(date +%Y%m%d_%H%M%S).log 2>&1
