#!/bin/bash
echo "Creating python environment"
python3 -m venv app/venv
source app/venv/bin/activate
echo "Installing pip dependencies"
pip install -r app/requirements.txt
echo "Downloading spacy package for POS Tagging"
python3 -m spacy download en_core_web_sm
echo "Running"
cd app
python3 -m uvicorn app:app --host 0.0.0.0 --port 8020
sleep 3
xdg-open http://localhost:8020 2>/dev/null || open http://localhost:8020 2>/dev/null