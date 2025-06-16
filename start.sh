#!/bin/bash
echo "Rebuildando tudo sem cache..."
docker-compose build --no-cache
echo "Subindo containers..."
docker-compose up
