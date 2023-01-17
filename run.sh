#!/bin/bash
export SCRAPER_DEST_DIR=target_local
mkdir $SCRAPER_DEST_DIR
source src/env/bin/activate
python3 src/main.py
