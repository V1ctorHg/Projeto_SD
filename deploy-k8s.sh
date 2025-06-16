#!/bin/bash

echo "Fazendo deploy no Kubernetes..."

# Build das imagens locais
echo "Buildando imagens..."
docker build -t voting-backend:latest ./backend
docker build -t voting-frontend:latest ./frontend

# Cleanup primeiro
echo "Limpando recursos antigos..."
kubectl delete namespace voting-system --ignore-not-found=true
kubectl wait --for=delete namespace/voting-system --timeout=60s 2>/dev/null || true

# Deploy no Kubernetes com ordem específica
echo "Aplicando manifestos..."
kubectl apply -f k8s/namespace.yaml
sleep 5

echo "Deployando Zookeeper..."
kubectl apply -f k8s/zookeeper.yaml
echo "Aguardando Zookeeper ficar pronto..."
kubectl wait --for=condition=available --timeout=180s deployment/zookeeper -n voting-system

# Verificar se Zookeeper está funcionando
echo "Testando Zookeeper..."
kubectl exec deployment/zookeeper -n voting-system -- sh -c "echo ruok | nc localhost 2181" || echo "Zookeeper pode não estar 100% pronto ainda"

echo "Deployando Kafka..."
kubectl apply -f k8s/kafka.yaml
echo "Aguardando Kafka ficar pronto (pode demorar 2-3 minutos)..."

# Esperar pods estarem rodando
kubectl wait --for=condition=available --timeout=300s deployment/kafka -n voting-system

echo "Verificando status do Kafka..."
kubectl get pods -n voting-system
kubectl logs deployment/kafka -n voting-system --tail=20

echo "Deployando Backend..."
kubectl apply -f k8s/backend.yaml
kubectl wait --for=condition=available --timeout=120s deployment/backend -n voting-system

echo "Deployando Frontend..."
kubectl apply -f k8s/frontend.yaml

echo "Deploy concluído!"
echo ""
echo "Status dos pods:"
kubectl get pods -n voting-system
echo ""
echo "Para acessar os serviços:"
echo "Frontend: kubectl port-forward -n voting-system service/frontend 4200:4200"
echo "Backend: kubectl port-forward -n voting-system service/backend 5001:5001"
echo ""
echo "Para ver logs:"
echo "kubectl logs -f deployment/kafka -n voting-system"
echo "kubectl logs -f deployment/backend -n voting-system"