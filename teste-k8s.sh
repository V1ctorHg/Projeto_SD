# Ver logs em tempo real
kubectl logs -f deployment/kafka -n voting-system
kubectl logs -f deployment/backend -n voting-system

# Ver status dos pods
kubectl get pods -n voting-system

# Testar conectividade
kubectl exec -it deployment/backend -n voting-system -- nc -z kafka 9092