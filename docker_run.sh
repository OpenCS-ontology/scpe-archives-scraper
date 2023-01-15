#!/bin/bash

mkdir target
docker run -d \
    -v target:/target \
    scpe_scraper
