#!/bin/bash

# [main] file
python3 -m venv env

source env/bin/activate
    pip3 install -r src/requirements.txt
    pyinstaller -F src/main.py
deactivate

mv dist/main ./
rmdir dist

# Docker
docker build -t scpe_scraper .

# Clean-up
rm -r build
rm -r env
rm main.spec
