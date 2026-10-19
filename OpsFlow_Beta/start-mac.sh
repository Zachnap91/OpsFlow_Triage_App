#!/bin/bash

#Find script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Launching OpsFlow Services..."

#Start backend API in new window
osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR/backend' && source .venv/bin/activate && uvicorn app.main:app --reload\""

#Start frontend UI in new window
osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR/frontend' && npm run dev\""

#Stall to let service initialize
sleep 3

#Open application in default browser
open http://localhost:5173
