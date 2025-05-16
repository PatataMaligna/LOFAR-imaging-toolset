#!/bin/bash

# Exit on any error
set -e

echo "Creating virtual environment..."
python3.12 -m venv envLofar
source envLofar/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "To start the app, run:"
echo "source envLofar/bin/activate && python3 -m realtime_processor.main /path/to/your/data"
