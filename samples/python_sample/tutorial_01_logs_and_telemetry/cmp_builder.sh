#!/bin/sh

## zip the data into a zip file
zip app.zip app/* \
            app/src/* \
            README.md \
            docker-compose.yml \
            app.json \
            images/*
