# 🗳️ Sistema de Votação - Cliente Dockerizado

Bem-vindo! Este é um sistema de votação completo, conteinerizado com Docker. Ele foi projetado para funcionar como um cliente de uma arquitetura distribuída, permitindo que usuários votem em candidatos e visualizem os resultados em tempo real através de uma interface web moderna.

## ✨ Principais Funcionalidades

-   **Interface Intuitiva:** Frontend em Angular para uma experiência de usuário fluida.
-   **Backend Robusto:** API em Python (Flask) para processar os votos.
-   **Pronto para a Nuvem:** Integra-se com serviços de mensageria (RabbitMQ) e um nó agregador externo.
-   **Acesso na Rede Local:** Permite acesso de qualquer dispositivo na sua rede.
-   **Fácil de Rodar:** Scripts prontos para iniciar e parar a aplicação com um único comando.

---

## 🏛️ Arquitetura e Fluxo de Dados

A aplicação utiliza o **Docker Compose** para orquestrar os serviços. O **Nginx**, dentro do contêiner do frontend, atua como um **Reverse Proxy**, redirecionando as chamadas de API para o backend. Isso é o que permite que a aplicação funcione perfeitamente quando acessada de outros dispositivos na rede.

```mermaid
graph TD;
    subgraph "Sua Rede Local"
        Device["📱 Outro Dispositivo"] -->|http://SEU_IP:4200| Nginx;
        User["👤 Usuário no PC"] -->|http://localhost:4200| Nginx;
    end

    subgraph "Seu PC (Docker)"
        Nginx["🌐 Nginx (Frontend)"] -->|Requisições /api/*| Backend["🐍 Backend (Flask)"];
        Nginx -->|Outras requisições| Angular["Aplicação Angular"];
    end

    subgraph "Serviços de Nuvem Externos"
        Backend -->|Publica Voto| RabbitMQ["🐇 CloudAMQP"];
        Backend -->|Busca Resultados| Aggregator["⚙️ Nó Agregador"];
        Aggregator -->|Processa de| RabbitMQ;
    end
```

---

## ✅ Pré-requisitos

Você só precisa de uma ferramenta instalada:

-   [**Docker**](https://www.docker.com/products/docker-desktop/): Inclui o Docker Compose (que já vem com o Docker Desktop para Windows e Mac).

---

## 🚀 Guia de Execução Passo a Passo

Siga estes passos para rodar a aplicação.

### Passo 1: Crie o Arquivo de Configuração (Obrigatório)

**Antes de tudo, você precisa configurar as variáveis de ambiente.** A aplicação depende de um arquivo `.env` na raiz do projeto para se conectar aos serviços de nuvem.

1.  Crie um arquivo chamado `.env` na pasta principal do projeto.
2.  Copie e cole o conteúdo abaixo dentro do arquivo `.env` que você acabou de criar.

```env
# Credenciais para o serviço de mensageria RabbitMQ (CloudAMQP)
RABBITMQ_HOST=chimpanzee.rmq.cloudamqp.com
RABBITMQ_PORT=5671
RABBITMQ_USERNAME=edxgujmk
RABBITMQ_PASSWORD=Wm1vy2ea99LIfZh-ZZyl3DhWlLDlNcdH
RABBITMQ_VIRTUAL_HOST=edxgujmk

# Fila padrão para publicação dos votos
RABBITMQ_QUEUE=lotes_de_dados

# Endereço do serviço que agrega e consolida os resultados
CORE_URL=https://agregador-node.onrender.com
```

> ⚠️ **Atenção:** A aplicação **não funcionará** sem este arquivo `.env` devidamente preenchido.

### Passo 2: Inicie a Aplicação com os Scripts

Com o arquivo `.env` criado, agora você pode usar os scripts para gerenciar os contêineres.

-   **Para a primeira execução ou para aplicar mudanças no código:**
    *Este comando reconstrói as imagens do Docker, garantindo que tudo esteja atualizado.*
    ```bash
    ./start.sh
    ```

-   **Para uma inicialização rápida (se as imagens já existem):**
    *Este comando apenas sobe os contêineres já existentes.*
    ```bash
    ./start-fast.sh
    ```

### Passo 3: Acesse a Aplicação
Após iniciar os contêineres, espere alguns instantes e acesse a interface no seu navegador:

-   **Endereço:** [**http://localhost:4200**](http://localhost:4200)

### Passo 4: Pare a Aplicação
Para parar todos os contêineres e limpar os recursos, use o comando:
```bash
./stop.sh
```

---

## 📁 Estrutura do Projeto

```
/
├── backend/            # Código da aplicação Backend (Python/Flask)
│   ├── app.py          # Arquivo principal da API
│   ├── dockerfile      # Define a imagem Docker do backend
│   └── ...
│
├── frontend/           # Código da aplicação Frontend (Angular)
│   ├── src/            # Código-fonte do Angular
│   └── dockerfile      # Define a imagem Docker do frontend
│
├── docker-compose.yml  # Orquestra os serviços de backend e frontend
├── .env                # (Você DEVE criar este arquivo) Credenciais
├── start.sh            # Script para CONSTRUIR e iniciar os contêineres
├── start-fast.sh       # Script para INICIAR contêineres já construídos
└── stop.sh             # Script para PARAR e limpar os contêineres
```

---

## 🌍 Acesso na Rede Local (de outros dispositivos)

Para testar em um celular, tablet ou outro computador na mesma rede:

#### 1. Encontre seu Endereço IP Local
   No Windows, abra o `cmd` ou `PowerShell` e digite `ipconfig`. No Mac/Linux, use `ifconfig` ou `ip addr`. Procure pelo seu **Endereço IPv4** (ex: `192.168.1.10`).

#### 2. Libere a Porta no Firewall (se necessário)
   Sistemas como o Windows podem bloquear conexões de entrada por padrão. Você precisa criar uma regra para permitir o tráfego na porta `4200`.
   -   **No Windows:**
        1.  Abra o **"Firewall do Windows com Segurança Avançada"**.
        2.  Vá para **"Regras de Entrada"** > **"Nova Regra..."**.
        3.  Selecione `Porta` > `TCP` > `Portas locais específicas: 4200`.
        4.  Selecione `Permitir a conexão` e aplique aos perfis de rede desejados (geralmente `Particular`).
        5.  Dê um nome à regra (ex: "Docker App") e salve.

#### 3. Acesse pelo outro dispositivo

Use o endereço IP do seu computador no navegador do outro dispositivo:

**Exemplo:** `http://192.168.1.10:4200`