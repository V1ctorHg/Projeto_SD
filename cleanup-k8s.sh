#!/bin/bash

echo "Removendo recursos do Kubernetes..."
kubectl delete namespace voting-system --timeout=60s
echo "Limpeza concluída!"