@echo off
echo Creating python environment
python -m venv app\venv
call app\venv\Scripts\activate
echo Installing pip dependencies
pip install -r app\requirements.txt
echo Downloading spacy package for POS Tagging
python -m spacy download en_core_web_sm
echo Running
cd app
python -m uvicorn app:app --host 0.0.0.0 --port 8020
timeout /t 3 /nobreak
start http://localhost:8020
pause