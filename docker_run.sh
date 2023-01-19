#!/bin/bash

mkdir target
chmod 755 target
docker run -d \
    -v $(pwd)/target:/target \
    scpe_scraper

