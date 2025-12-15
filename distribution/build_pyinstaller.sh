#!/bin/sh
set -e
if [ ! -d  distribution ] || [ ! -f assets/oscr_icon_small.png ]
then
  echo "[Error] Start this script from the base folder of the application"
  exit
fi

echo "[Info]  Checking for existing venv \".venv\""
if [ ! -d ".venv" ]
then
  echo "[Info]  No venv found. Creating venv \".venv\"..."
  python3 -m venv .venv
fi

echo "[Info]  Activating venv."
. ".venv/bin/activate"

echo "[Info]  Installing dependencies."
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -e .

echo "[Info]  Install PyInstaller build tool."
python3 -m pip install "pyinstaller==6.10.0"

echo "[Info]  Creating binary app."
pyinstaller --noconfirm --clean --onedir --name OSCR-UI main.py \
  --add-data assets:assets --add-data locales:locales --windowed \
  --icon assets/oscr_icon_small.png

echo "[Info]  Leaving venv."
deactivate
