#!/bin/bash

#Find script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

#Navigate to backend directory
cd "$SCRIPT_DIR/backend"

#Create and activate virtual environment with python
python3.12 -m venv .venv
source .venv/bin/activate

#Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements-dev.txt

#Navigate to frontend directory
cd "$SCRIPT_DIR/frontend"

#Install frontend dependencies
npm install

echo ""
echo "Setup complete. Run ./start-mac.sh to launch OpsFlow."
