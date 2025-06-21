#!/bin/bash

echo "Derrubando containers e limpando volumes..."
docker-compose down -v

echo "Limpando imagens dangling (sem tag)..."
docker image prune -f

echo "Reset completo!"


