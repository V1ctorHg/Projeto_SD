#!/bin/bash

echo "Subindo containers (sem rebuild)..."
docker-compose up -d

echo "Containers em execução!"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

