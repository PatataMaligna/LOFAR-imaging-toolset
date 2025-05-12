#!/bin/bash

# Exit on any error
set -e

echo "Creating virtual environment..."
python3 -m venv envLofar
source envLofar/bin/activate

echo "Installing system dependencies..."
sudo apt update
sudo apt install -y libgl1 libglib2.0-0

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install git+https://github.com/lofar-astron/lofarimaging.git
cd realtime_processor
pip install -r requirements.txt
cd ..

echo "To start the app, run:"
echo "source envLofar/bin/activate && python3 -m realtime_processor.main /path/to/your/data"
