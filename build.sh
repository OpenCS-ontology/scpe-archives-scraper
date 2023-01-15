#!/bin/bash

python3 -m venv env
source env/bin/activate

pip3 install -r src/requirements.txt
pyinstaller -F src/main.py

rm -r build
mv dist/main ./
rmdir dist
rm main.spec
deactivate
rm -r env
