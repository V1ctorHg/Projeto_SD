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
import ssl

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
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'chimpanzee.rmq.cloudamqp.com')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5671))
RABBITMQ_USERNAME = os.getenv('RABBITMQ_USERNAME', 'edxgujmk')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'Wm1vy2ea99LIfZh-ZZyl3DhWlLDlNcdH')
RABBITMQ_QUEUE = os.getenv('RABBITMQ_QUEUE', 'lotes_de_dados')
RABBITMQ_VIRTUAL_HOST = os.getenv('RABBITMQ_VIRTUAL_HOST', 'edxgujmk')  # importante!


CORE_URL = os.getenv('CORE_URL', 'https://agregador-node.onrender.com')
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
        self._connect()  # Conecta na inicialização

    def _connect(self):
        """
        Estabelece a conexão e o canal com o RabbitMQ.
        Este método é privado e deve ser chamado internamente.
        """
        try:
            if self.connection and self.connection.is_open:
                return  # Já estamos conectados

            logger.info("Tentando conectar ao RabbitMQ...")
            credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
            ssl_context = ssl.create_default_context()
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                virtual_host=RABBITMQ_VIRTUAL_HOST,
                credentials=credentials,
                ssl_options=pika.SSLOptions(ssl_context),
                heartbeat=300, # Heartbeat para manter a conexão viva
                blocked_connection_timeout=150
            )

            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
            logger.info("✅ Conectado ao RabbitMQ com sucesso!")

        except Exception as e:
            logger.error(f"❌ Falha catastrófica ao conectar ao RabbitMQ: {e}")
            self.connection = None
            self.channel = None

    def _ensure_connection(self):
        """Garante que a conexão está ativa antes de uma operação."""
        if not self.connection or not self.connection.is_open or not self.channel or not self.channel.is_open:
            logger.warning("Conexão com RabbitMQ perdida. Tentando reconectar...")
            self._connect()

    def enviar_mensagem(self, mensagem):
        """
        Envia uma mensagem para a fila, com tentativas de reconexão.
        """
        self._ensure_connection()
        
        if not self.channel:
            logger.error("❌ Não foi possível enviar mensagem: canal indisponível após tentativa de reconexão.")
            return False

        try:
            mensagem_json = json.dumps(mensagem)
            self.channel.basic_publish(
                exchange='',
                routing_key=RABBITMQ_QUEUE,
                body=mensagem_json,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            logger.info(f"📤 Mensagem enviada para RabbitMQ: {mensagem['batchId']}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem: {e}. A conexão pode ter sido perdida.")
            # A próxima chamada irá tentar reconectar através do _ensure_connection
            self.connection = None # Força a reconexão na próxima chamada
            self.channel = None
            return False

    def close(self):
        """Fecha a conexão de forma limpa."""
        if self.connection and self.connection.is_open:
            logger.info("Fechando conexão com RabbitMQ...")
            self.connection.close()

# Instância única para ser usada por toda a aplicação
rabbitmq_manager = RabbitMQManager()

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
    for cidade in resultados:
        votos_por_partido = cidade.get("votos_por_partido", {})
        for partido, votos in votos_por_partido.items():
            for _ in range(votos):
                lote = gerar_lote("eleicao", partido)
                if rabbitmq_manager.enviar_mensagem(lote):
                    total_enviados += 1
                else:
                    logger.error(f"[SIMULAÇÃO] Falha ao enviar voto para {partido}")
            logger.info(f"[SIMULAÇÃO] Enviados {votos} votos para {partido}")
    logger.info(f"[SIMULAÇÃO] Total de votos enviados: {total_enviados}")

@app.route('/votar', methods=['POST'])
def votar():
    try:
        dados = request.get_json()
        cpf = dados.get('cpf')
        candidato = dados.get('candidato_id')
        tipo = 'eleicao'

        if not candidato:
            return jsonify({"erro": "Candidato não informado"}), 400

        if not cpf or not candidato:
            return jsonify({"erro": "CPF e candidato_id são obrigatórios"}), 400

        # Limpa o CPF de caracteres não numéricos
        cpf = ''.join(filter(str.isdigit, str(cpf)))

        # Caminho do arquivo persistente
        arquivo_cpfs = os.path.join(os.path.dirname(__file__), 'data', 'cpfs_votantes.json')


        # Garante que o arquivo exista e leia os dados
        if not os.path.exists(arquivo_cpfs):
            with open(arquivo_cpfs, 'w') as f:
                json.dump([], f)

        with open(arquivo_cpfs, 'r') as f:
            try:
                cpfs_votantes = json.load(f)
            except json.JSONDecodeError:
                cpfs_votantes = []

        if cpf in cpfs_votantes:
            return jsonify({"erro": "CPF já votou"}), 403

        if not candidato_existe(candidato):
            return jsonify({"erro": "Candidato inválido"}), 400

        # Gera e envia o voto
        lote = gerar_lote(tipo, candidato)
        if rabbitmq_manager.enviar_mensagem(lote):
            cpfs_votantes.append(cpf)
            with open(arquivo_cpfs, 'w') as f:
                json.dump(cpfs_votantes, f)
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
            return jsonify({"resultados": [], "eleicaoativa": False})
        dados_gerais = response.json()
        dados_agregados = dados_gerais.get("dadosAgregados", [])

        dados_eleicao = None
        for item in dados_agregados:
            if item.get("type") == "eleicao":
                dados_eleicao = item.get("lista", [])
                break
        
        if not dados_eleicao:
            return jsonify({"resultados": [], "eleicaoativa": True})

        resultados_formatados = []
        for resultado in dados_eleicao:
            # O agregador retorna 'objectIdentifier' e 'somatorio'
            # O frontend espera 'id', 'nome', e 'votos'
            resultados_formatados.append({
                "id": resultado.get("objectIdentifier"), 
                "nome": resultado.get("objectIdentifier"), 
                "votos": resultado.get("somatorio", 0)
            })

        resposta_final = {
            "resultados": resultados_formatados,
            "eleicaoativa": True # Assumindo que a eleição está sempre ativa
        }

        resultados_cache["dados"] = resposta_final
        resultados_cache["timestamp"] = agora
        
        return jsonify(resposta_final)

    except Exception as e:
        logger.error(f"Erro ao buscar resultados: {str(e)}")
        return jsonify({"resultados": [], "eleicaoativa": False})

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
        # rabbitmq = get_rabbitmq_manager() # Não é mais necessário
        # Uma forma simples de checar a saúde é garantir que o canal está aberto
        if rabbitmq_manager.channel and rabbitmq_manager.channel.is_open:
            rabbitmq_status = "connected"
        else:
            rabbitmq_status = "disconnected"

        response = requests.get(f"{AGGREGATOR_URL}/actuator/health", timeout=5)
        return jsonify({
            "status": "healthy",
            "rabbitmq": rabbitmq_status,
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
    # A instância do RabbitMQManager já é criada e tenta se conectar na inicialização.
    # Não precisamos chamar get_rabbitmq_manager() aqui.
    if rabbitmq_manager.channel:
        logger.info("Backend iniciado com conexão ao RabbitMQ estabelecida.")
    else:
        logger.warning("Backend iniciado, mas sem conexão com RabbitMQ. Tentativas de reconexão ocorrerão.")
    
    waitress.serve(app, host='0.0.0.0', port=5001, threads=32)
