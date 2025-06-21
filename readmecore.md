# 🚀 Aggregator Node - Sistema de Agregação de Dados

## 📋 Índice
1. [O que é este projeto?](#o-que-é-este-projeto)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Como Rodar o Projeto](#como-rodar-o-projeto)
4. [Endpoints da API](#endpoints-da-api)
5. [Formato das Mensagens](#formato-das-mensagens)
6. [Como Conectar seu Backend](#como-conectar-seu-backend)
7. [Estrutura do Banco de Dados](#estrutura-do-banco-de-dados)
8. [Configurações](#configurações)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 O que é este projeto?

Este é um **sistema de agregação de dados** desenvolvido em **Spring Boot** que:

- ✅ Recebe lotes de dados via **RabbitMQ**
- ✅ Processa e agrega os dados automaticamente
- ✅ Salva tudo no **PostgreSQL**
- ✅ Disponibiliza resultados via **REST API**
- ✅ Envia atualizações em tempo real via **WebSocket**
- ✅ Calcula estatísticas (média, mediana, soma, contagem, porcentagem)

**Em português simples**: É um "processador inteligente" que recebe dados de vários lugares, faz cálculos e disponibiliza os resultados de várias formas.

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SEU BACKEND   │───▶│   RABBITMQ      │───▶│  AGGREGATOR     │
│   (Produtor)    │    │   (Fila)        │    │   NODE          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SEU FRONTEND  │◀───│   WEBSOCKET     │◀───│   POSTGRESQL    │
│   (Consumidor)  │    │   (Tempo Real)  │    │   (Banco)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Componentes Principais:

1. **MessageListener**: Escuta a fila RabbitMQ e processa os dados
2. **AggregationService**: Faz os cálculos e salva no banco
3. **Publisher**: Publica resultados atualizados
4. **Consumer**: Envia dados via WebSocket
5. **AggregatorController**: API REST para consultar resultados

---

## 🚀 Como Rodar o Projeto

### Pré-requisitos:
- Docker e Docker Compose instalados
- Java 21 (se quiser rodar localmente)
- Gradle (se quiser rodar localmente)

### Opção 1: Com Docker (RECOMENDADO)

1. **Clone o projeto:**
```bash
git clone <url-do-repositorio>
cd agregador-node-springboot
```

2. **Crie a rede Docker:**
```bash
docker network create rede
```

3. **Suba todos os serviços:**
```bash
docker-compose up -d
```

4. **Verifique se tudo está rodando:**
```bash
docker-compose ps
```

### Opção 2: Localmente

1. **Configure as variáveis de ambiente:**
```bash
export SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/AgregadorDB
export SPRING_DATASOURCE_USERNAME=postgres
export SPRING_DATASOURCE_PASSWORD=root
export SPRING_RABBITMQ_HOST=localhost
export SPRING_RABBITMQ_USERNAME=guest
export SPRING_RABBITMQ_PASSWORD=guest
```

2. **Rode o projeto:**
```bash
./gradlew bootRun
```

### 🎯 URLs Importantes:

- **Aplicação**: http://localhost:8080
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)
- **Health Check**: http://localhost:8080/actuator/health
- **WebSocket**: ws://localhost:8080/ws

---

## 📡 Endpoints da API

### 1. GET `/api/aggregator/results`
**O que faz:** Retorna todos os dados agregados

**Resposta:**
```json
{
  "dadosAgregados": [
    {
      "tipo": "temperatura",
      "estatisticas": [
        {
          "identificadorObjeto": "sensor-001",
          "media": 25.5,
          "mediana": 25.0,
          "somatorio": 255.0,
          "contagem": 10,
          "porcentagem": 45.2
        }
      ]
    }
  ],
  "totalLotesProcessadosGlobal": 5,
  "totalItensDeDadosProcessadosGlobal": 150
}
```

**Como testar:**
```bash
curl http://localhost:8080/api/aggregator/results
```

---

## 📨 Formato das Mensagens

### Mensagem que o sistema ESPERA receber:

```json
{
  "batchId": "lote-123",
  "sourceNodeId": "node-001",
  "dataPoints": [
    {
      "type": "temperatura",
      "objectIdentifier": "sensor-001",
      "valor": 25.5,
      "eventDatetime": "2024-01-15T10:30:00"
    },
    {
      "type": "umidade",
      "objectIdentifier": "sensor-002",
      "valor": 60.0,
      "eventDatetime": "2024-01-15T10:30:00"
    }
  ]
}
```

### Campos Obrigatórios:
- `batchId`: ID único do lote (string)
- `sourceNodeId`: ID do nó que enviou (string)
- `dataPoints`: Array de dados
  - `type`: Tipo do dado (string)
  - `objectIdentifier`: Identificador do objeto (string)
  - `valor`: Valor numérico (double)
  - `eventDatetime`: Data/hora do evento (ISO 8601)

---

## 🔌 Como Conectar seu Backend

### 1. Configurar RabbitMQ no seu backend:

```java
// Exemplo em Java/Spring
@Configuration
public class RabbitMQConfig {
    
    @Bean
    public Queue queue() {
        return new Queue("lotes_de_dados", true);
    }
    
    @Bean
    public RabbitTemplate rabbitTemplate(ConnectionFactory connectionFactory) {
        RabbitTemplate template = new RabbitTemplate(connectionFactory);
        template.setMessageConverter(new Jackson2JsonMessageConverter());
        return template;
    }
}
```

### 2. Enviar mensagens:

```java
@Service
public class DataSenderService {
    
    @Autowired
    private RabbitTemplate rabbitTemplate;
    
    public void enviarLote(IncomingDataBatch lote) {
        rabbitTemplate.convertAndSend("lotes_de_dados", lote);
    }
}
```

### 3. Exemplo de uso:

```java
// Criar um lote de dados
IncomingDataBatch lote = new IncomingDataBatch();
lote.setBatchId("lote-" + System.currentTimeMillis());
lote.setSourceNodeId("meu-backend");
lote.setDataPoints(Arrays.asList(
    new GenericDataItem("temperatura", "sensor-001", 25.5, LocalDateTime.now()),
    new GenericDataItem("umidade", "sensor-002", 60.0, LocalDateTime.now())
));

// Enviar para o aggregator
dataSenderService.enviarLote(lote);
```

### 4. Receber dados via WebSocket (Frontend):

```javascript
// Conectar ao WebSocket
const socket = new SockJS('http://localhost:8080/ws');
const stompClient = Stomp.over(socket);

stompClient.connect({}, function (frame) {
    console.log('Conectado ao WebSocket');
    
    // Inscrever para receber dados agregados
    stompClient.subscribe('/topic/aggregated', function (message) {
        const dados = JSON.parse(message.body);
        console.log('Dados recebidos:', dados);
        // Atualizar sua interface aqui
    });
});
```

---

## 🗄️ Estrutura do Banco de Dados

### Tabela: `generic_data_records`
```sql
CREATE TABLE generic_data_records (
    id BIGSERIAL PRIMARY KEY,
    data_type VARCHAR(255),
    object_identifier VARCHAR(255),
    valor DOUBLE PRECISION,
    event_datetime TIMESTAMP,
    batch_id VARCHAR(255)
);
```

### Tabela: `processed_batches`
```sql
CREATE TABLE processed_batches (
    batch_id VARCHAR(255) PRIMARY KEY
);
```

### Índices:
- `idx_datatype_objectidentifier` em (data_type, object_identifier)

---

## ⚙️ Configurações

### Variáveis de Ambiente:

```properties
# Banco de Dados
SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/AgregadorDB
SPRING_DATASOURCE_USERNAME=postgres
SPRING_DATASOURCE_PASSWORD=root

# RabbitMQ
SPRING_RABBITMQ_HOST=localhost
SPRING_RABBITMQ_USERNAME=guest
SPRING_RABBITMQ_PASSWORD=guest

# Filas
RABBITMQ_QUEUE_NAME=lotes_de_dados
RABBITMQ_QUEUE_WEBSOCKET_NAME=websocket_all
```

### Filas RabbitMQ:
- `lotes_de_dados`: Recebe os lotes de dados
- `websocket_all`: Envia dados para WebSocket

---

## 🔧 Troubleshooting

### Problema: "Connection refused" no RabbitMQ
**Solução:**
```bash
# Verificar se o RabbitMQ está rodando
docker-compose ps rabbitmq

# Reiniciar o serviço
docker-compose restart rabbitmq
```

### Problema: "Database connection failed"
**Solução:**
```bash
# Verificar se o PostgreSQL está rodando
docker-compose ps postgres-db

# Verificar logs
docker-compose logs postgres-db
```

### Problema: "Queue not found"
**Solução:**
1. Acesse http://localhost:15672
2. Login: guest/guest
3. Verifique se as filas existem
4. Se não existirem, reinicie a aplicação

### Problema: WebSocket não conecta
**Solução:**
```javascript
// Verificar se a URL está correta
const socket = new SockJS('http://localhost:8080/ws');

// Verificar se o endpoint está correto
stompClient.subscribe('/topic/aggregated', function (message) {
    // ...
});
```

---

## 📊 Monitoramento

### Health Checks:
- http://localhost:8080/actuator/health
- http://localhost:8080/actuator/metrics
- http://localhost:8080/actuator/prometheus

### Logs:
```bash
# Ver logs da aplicação
docker-compose logs agregador-node

# Ver logs em tempo real
docker-compose logs -f agregador-node
```

---

## 🎯 Resumo para Desenvolvedores

### Para ENVIAR dados:
1. Configure RabbitMQ no seu backend
2. Envie mensagens no formato JSON para a fila `lotes_de_dados`
3. Use o formato `IncomingDataBatch`

### Para RECEBER dados:
1. **REST API**: GET `/api/aggregator/results`
2. **WebSocket**: Conecte em `ws://localhost:8080/ws` e inscreva em `/topic/aggregated`

### Para TESTAR:
1. Use o RabbitMQ Management (http://localhost:15672)
2. Envie mensagens de teste via interface web
3. Verifique os resultados na API REST

---

## 🚨 Importante!

- ✅ O sistema processa dados automaticamente quando recebe na fila
- ✅ Cada lote deve ter um `batchId` único
- ✅ Dados duplicados são ignorados
- ✅ WebSocket envia atualizações em tempo real
- ✅ API REST sempre retorna dados atualizados

---

**🎉 Agora você está pronto para conectar seu backend ao Aggregator Node!** 