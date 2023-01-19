#!/bin/bash

mkdir target
docker run -d \
    -v $(pwd)/target:/target \
    scpe_scraper

