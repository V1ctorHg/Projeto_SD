# 🗳️ Sistema de Votação Distribuído

Este projeto implementa um cliente para um sistema de votação distribuído. Ele consiste em uma interface de usuário (frontend) para registrar votos e uma aplicação de retaguarda (backend) que envia esses votos para um nó agregador central para processamento.

## 🏛️ Arquitetura

A arquitetura de desenvolvimento local segue o seguinte fluxo:

```mermaid
graph TD;
    Usuario[👤 Usuário] -->|Vota em| Frontend;
    Frontend[🌐 Frontend Angular] -->|Envia voto via API| Backend;
    Backend[🐍 Backend Flask] -->|Publica mensagem| RabbitMQ;
    RabbitMQ[🐇 RabbitMQ] -->|Consumido por| AggregatorNode[⚙️ Aggregator Node (Externo)];
```

**Nota sobre Kubernetes:** A arquitetura alvo para produção no Kubernetes pretende substituir o RabbitMQ por Kafka. No entanto, a implementação atual do backend **não é compatível** com essa configuração, tornando o desdobramento via Kubernetes não funcional no momento.

---

## ✨ Tecnologias Principais

- **Frontend:** Angular
- **Backend:** Python (Flask)
- **Mensageria:** RabbitMQ (para Docker) / Kafka (alvo para K8s)
- **Containerização:** Docker, Docker Compose
- **Orquestração:** Kubernetes

---

## 📁 Estrutura do Projeto

```
/
├── frontend/       # Aplicação Frontend em Angular
├── backend/        # Aplicação Backend em Python (Flask)
├── k8s/            # Manifestos de desdobramento para Kubernetes
├── docker-compose.yml # Orquestração dos serviços para ambiente local
├── start.sh        # Script para construir e iniciar containers (Docker)
├── stop.sh         # Script para parar e limpar containers (Docker)
└── deploy-k8s.sh   # Script para desdobrar a aplicação no Kubernetes (atualmente não funcional)
```

---

## 🚀 Executando com Docker (Método Recomendado e Funcional)

Esta é a **única** forma garantida para executar o projeto corretamente.

### ✅ Pré-requisitos
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) ou Docker Engine/Compose para Linux.
- Acesso a uma instância do **Nó Agregador** e do **RabbitMQ**. Esses serviços podem estar:
  - Rodando localmente em uma rede Docker externa (ex: `rede`).
  - Acessíveis remotamente através de um endereço IP ou hostname. **(Este é o cenário alvo para produção)**

### ⚙️ Configuração
Antes de iniciar, crie um arquivo chamado `.env` na raiz do projeto, baseado no exemplo abaixo. Este arquivo fornecerá as variáveis de ambiente necessárias para o backend se conectar aos outros serviços.

**`.env.example`**:
```env
# URL do nó agregador que recebe os dados
CORE_URL=http://<IP_OU_HOSTNAME_DO_AGREGADOR>:8080

# Detalhes de conexão do RabbitMQ
RABBITMQ_HOST=<IP_OU_HOSTNAME_DO_RABBITMQ>
RABBITMQ_PORT=5672
RABBITMQ_USERNAME=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_QUEUE=lotes_de_dados
```

### ▶️ Iniciando a Aplicação

Para construir as imagens e iniciar os containers, execute:
```bash
./start.sh
```
Se você não fez alterações no código e só quer subir os containers, use a versão rápida:
```bash
./start-fast.sh
```
### ⏹️ Parando a Aplicação

Para parar todos os containers e limpar os recursos, execute:
```bash
./stop.sh
```

### 🌐 Acessos

| Serviço    | Endereço Local                          |
|------------|-----------------------------------------|
| Frontend   | [http://localhost:4200](http://localhost:4200) |
| Backend API| [http://localhost:5001](http://localhost:5001) |

---

## ☸️ Desdobrando no Kubernetes (NÃO UTILIZAR - DESATUALIZADO)

> 🛑 **AVISO:** Esta configuração está **desatualizada e não é funcional**. O backend atual **não se conecta** ao Kafka, que é o sistema de mensageria usado nesta configuração. Use esta seção apenas como referência para desenvolvimento futuro.

### ⚠️ Motivo da Incompatibilidade
A configuração do Kubernetes (`k8s/`) desdobra Zookeeper e Kafka. No entanto, a aplicação backend só possui código para se conectar ao RabbitMQ. Portanto, o envio de votos **falhará** neste desdobramento.

### ✅ Pré-requisitos (para referência)
- `kubectl` configurado para acessar seu cluster Kubernetes.
- Permissão para criar `namespace`, `deployments`, e `services`.

### ▶️ Desdobramento
O script a seguir irá construir as imagens Docker locais e aplicar todos os manifestos do Kubernetes na ordem correta:
```bash
./deploy-k8s.sh
```

### 🧹 Limpeza
Para remover todos os recursos criados no cluster pelo script de desdobramento, execute:
```bash
./cleanup-k8s.sh
```

### 🌐 Acessando os Serviços no Kubernetes
Após o desdobramento, você pode acessar os serviços usando `port-forward`:
```bash
# Para o Frontend
kubectl port-forward -n voting-system service/frontend 4200:80

# Para o Backend
kubectl port-forward -n voting-system service/backend 5001:5001
```

---

*Este README foi gerado e atualizado para refletir o estado atual do projeto.*
