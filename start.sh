#!/bin/bash

echo "Rebuildando tudo sem cache..."
docker-compose --env-file .env build --no-cache

echo "Subindo containers..."
docker-compose --env-file .env up -d

