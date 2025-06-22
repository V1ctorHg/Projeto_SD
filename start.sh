#!/bin/bash

echo "Rebuildando tudo sem cache..."
docker-compose build --no-cache

echo "Subindo containers..."
docker-compose up -d

echo "Containers em execução!"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

