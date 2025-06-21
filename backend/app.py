from flask import Flask, jsonify, request
from flask_cors import CORS
import waitress
import requests
import threading
from eleicoesalternativo import eleicao
from datetime import datetime, timedelta
import logging
import json
import sys
import uuid
import pika
import os

app = Flask(__name__)
CORS(app)

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# === CONFIGURAÇÕES MODULARES DO RABBITMQ ===
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USERNAME = os.getenv('RABBITMQ_USERNAME', 'guest')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')
RABBITMQ_QUEUE = os.getenv('RABBITMQ_QUEUE', 'lotes_de_dados')
RABBITMQ_VIRTUAL_HOST = "/"

CORE_URL = os.getenv('CORE_URL', 'http://localhost:8080')
AGGREGATOR_URL = CORE_URL

logger.info(f"=== CONFIGURAÇÕES CARREGADAS ===")
logger.info(f"RABBITMQ_HOST: {RABBITMQ_HOST}")
logger.info(f"RABBITMQ_PORT: {RABBITMQ_PORT}")
logger.info(f"RABBITMQ_USERNAME: {RABBITMQ_USERNAME}")
logger.info(f"RABBITMQ_QUEUE: {RABBITMQ_QUEUE}")
logger.info(f"CORE_URL: {CORE_URL}")
logger.info(f"AGGREGATOR_URL: {AGGREGATOR_URL}")
logger.info(f"===============================")

CACHE_DURACAO = 30
CANDIDATOS_PATH = "candidatos.json"

class RabbitMQManager:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self):
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
            logger.info("Conectado ao RabbitMQ com sucesso!")
        except Exception as e:
            logger.error(f"Erro ao conectar ao RabbitMQ: {e}")
            raise

    def enviar_mensagem(self, mensagem):
        try:
            if not self.connection or self.connection.is_closed:
                self.connect()
            mensagem_json = json.dumps(mensagem)
            self.channel.basic_publish(
                exchange='',
                routing_key=RABBITMQ_QUEUE,
                body=mensagem_json,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            logger.info(f"Mensagem enviada para RabbitMQ: {mensagem['batchId']}")
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para RabbitMQ: {e}")
            try:
                self.connect()
                return self.enviar_mensagem(mensagem)
            except:
                return False

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()

rabbitmq_manager = None

def get_rabbitmq_manager():
    global rabbitmq_manager
    if rabbitmq_manager is None:
        rabbitmq_manager = RabbitMQManager()
    return rabbitmq_manager

def carregar_candidatos():
    try:
        with open(CANDIDATOS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar candidatos: {e}")
        return []

def candidato_existe(candidato_id):
    candidatos = carregar_candidatos()
    return any(c["id"] == candidato_id for c in candidatos)

def gerar_lote(tipo, candidato_nome):
    return {
        "batchId": f"VOTO_{uuid.uuid4().hex[:8]}",
        "sourceNodeId": "GRUPO_1",
        "dataPoints": [
            {
                "type": tipo,
                "objectIdentifier": candidato_nome,
                "valor": 1,
                "eventDatetime": datetime.now().isoformat()
            }
        ]
    }

resultados_cache = {
    "timestamp": None,
    "dados": None
}

def processar_eleicao(data):
    try:
        candidatos = [c["id"] for c in carregar_candidatos()]
        logger.info(f"[SIMULAÇÃO] Candidatos disponíveis: {candidatos}")
        resultados_cidades = eleicao.processar_eleicao(data["num_cidades"], candidatos, data["populacao_total"])
        enviar_resultados(resultados_cidades)
    except Exception as e:
        logger.error(f"[SIMULAÇÃO] Erro durante a simulação: {str(e)}")

def enviar_resultados(resultados):
    total_enviados = 0
    rabbitmq = get_rabbitmq_manager()
    for cidade in resultados:
        votos_por_partido = cidade.get("votos_por_partido", {})
        for partido, votos in votos_por_partido.items():
            for _ in range(votos):
                lote = gerar_lote("eleicao", partido)
                if rabbitmq.enviar_mensagem(lote):
                    total_enviados += 1
                else:
                    logger.error(f"[SIMULAÇÃO] Falha ao enviar voto para {partido}")
            logger.info(f"[SIMULAÇÃO] Enviados {votos} votos para {partido}")
    logger.info(f"[SIMULAÇÃO] Total de votos enviados: {total_enviados}")

@app.route('/votar', methods=['POST'])
def votar():
    try:
        dados = request.json
        candidato = dados.get('candidato_id')
        tipo = 'eleicao'
        if not candidato:
            return jsonify({"erro": "Candidato não informado"}), 400
        if not candidato_existe(candidato):
            return jsonify({"erro": "Candidato inválido"}), 400
        lote = gerar_lote(tipo, candidato)
        rabbitmq = get_rabbitmq_manager()
        if rabbitmq.enviar_mensagem(lote):
            return jsonify({"status": "Voto enviado com sucesso"}), 200
        else:
            return jsonify({"erro": "Erro ao enviar para o RabbitMQ"}), 500
    except Exception as e:
        logger.error(f"Erro ao processar voto: {str(e)}")
        return jsonify({"erro": "Erro interno"}), 500

@app.route('/resultados', methods=['GET'])
def resultados():
    try:
        agora = datetime.now()
        if resultados_cache["timestamp"] and agora - resultados_cache["timestamp"] < timedelta(seconds=CACHE_DURACAO):
            logger.info("Retornando resultados do cache.")
            return jsonify(resultados_cache["dados"])
        logger.info("Buscando novos resultados do Aggregator Node...")
        response = requests.get(f"{AGGREGATOR_URL}/api/aggregator/results", timeout=10)
        if response.status_code != 200:
            logger.warning("Erro ao buscar resultados do agregador.")
            return jsonify({"dadosAgregados": [], "totalLotesProcessadosGlobal": 0, "totalItensDeDadosProcessadosGlobal": 0})
        dados_gerais = response.json()
        dados_agregados = dados_gerais.get("dadosAgregados", [])
        meus_dados = [item for item in dados_agregados if item["tipo"] in ["eleicao"]]
        resposta_filtrada = {
            "dadosAgregados": meus_dados,
            "totalLotesProcessadosGlobal": dados_gerais.get("totalLotesProcessadosGlobal"),
            "totalItensDeDadosProcessadosGlobal": dados_gerais.get("totalItensDeDadosProcessadosGlobal")
        }
        resultados_cache["dados"] = resposta_filtrada
        resultados_cache["timestamp"] = agora
        return jsonify(resposta_filtrada)
    except Exception as e:
        logger.error(f"Erro ao buscar resultados: {str(e)}")
        return jsonify({"dadosAgregados": [], "totalLotesProcessadosGlobal": 0, "totalItensDeDadosProcessadosGlobal": 0})

@app.route('/electionalternative', methods=['POST'])
def electionalternative():
    try:
        data = request.json
        logger.info(f"[SIMULAÇÃO] Dados recebidos: {data}")
        threading.Thread(target=processar_eleicao, args=(data,), daemon=True).start()
        return jsonify({"message": "Simulação iniciada em background"})
    except Exception as e:
        logger.error(f"[SIMULAÇÃO] Erro ao iniciar simulação: {e}")
        return jsonify({"erro": "Erro ao iniciar simulação"}), 500


@app.route('/candidatos', methods=['GET'])
def get_candidatos():
    try:
        candidatos = carregar_candidatos()
        logger.info(f"[CANDIDATOS] Lista enviada com {len(candidatos)} candidatos.")
        return jsonify(candidatos)
    except Exception as e:
        logger.error(f"[CANDIDATOS] Erro ao obter candidatos: {e}")
        return jsonify({"erro": "Erro interno ao obter candidatos"}), 500



@app.route('/health', methods=['GET'])
def health():
    try:
        rabbitmq = get_rabbitmq_manager()
        response = requests.get(f"{AGGREGATOR_URL}/actuator/health", timeout=5)
        return jsonify({
            "status": "healthy",
            "rabbitmq": "connected",
            "aggregator_node": "connected" if response.status_code == 200 else "disconnected"
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.route('/')
def index():
    return jsonify({"message": "API de votação rodando!"})

if __name__ == "__main__":
    print("INICIANDO SCRIPT app.py")
    try:
        get_rabbitmq_manager()
        logger.info("Backend iniciado com sucesso!")
    except Exception as e:
        logger.error(f"Erro ao inicializar RabbitMQ: {e}")
        print("Certifique-se de que o RabbitMQ está rodando!")
    waitress.serve(app, host='0.0.0.0', port=5001, threads=32)
