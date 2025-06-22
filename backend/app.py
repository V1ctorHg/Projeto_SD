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
import atexit
import time

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
CANDIDATOS_PATH = os.path.join(os.path.dirname(__file__), 'data', 'candidatos.json')
MAX_BATCH = 30
INTERVALO_ENVIO = 20
PENDENTES_PATH = os.path.join(os.path.dirname(__file__), 'data', 'lotes_pendentes.json')
ARQUIVO_LOCK = threading.Lock()
INTERVALO_REENVIO = 60

class FilaRabbit:
    def __init__(self):
        self.conn = None
        self.ch = None
        self._conectar()

    def _conectar(self):
        if self.conn and self.conn.is_open:
            return
        try:
            logger.info("🔌 Conectando ao RabbitMQ...")
            cred = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
            ssl_ctx = ssl.create_default_context()
            params = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                virtual_host=RABBITMQ_VIRTUAL_HOST,
                credentials=cred,
                ssl_options=pika.SSLOptions(ssl_ctx),
                heartbeat=300,
                blocked_connection_timeout=150
            )
            self.conn = pika.BlockingConnection(params)
            self.ch = self.conn.channel()
            self.ch.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
            logger.info("✅ Conectado com sucesso!")
        except Exception as e:
            logger.error(f"💥 Erro na conexão: {e}")
            self.conn = None
            self.ch = None

    def _checar_conexao(self):
        if not self.conn or not self.conn.is_open or not self.ch or not self.ch.is_open:
            logger.warning("⚠️ Conexão perdida. Tentando reconectar...")
            self._conectar()

    def mandar(self, pacote):
        self._checar_conexao()
        if not self.ch:
            logger.error("❌ Canal indisponível. Mensagem não enviada.")
            return False
        try:
            corpo = json.dumps(pacote)
            self.ch.basic_publish(
                exchange='',
                routing_key=RABBITMQ_QUEUE,
                body=corpo,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            logger.info(f"📨 Lote enviado: {pacote['batchId']}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro no envio: {e}")
            self.conn = None
            self.ch = None
            return False

    def fechar(self):
        if self.conn and self.conn.is_open:
            logger.info("Encerrando conexão com RabbitMQ...")
            self.conn.close()

class EnviadorLote:
    def __init__(self, fila, tamanho_max, intervalo):
        self.fila = fila
        self.tamanho_max = tamanho_max
        self.intervalo = intervalo
        self.buffer = []
        self.lock = threading.RLock()
        self.timer = None
        self._agendar()

    def _agendar(self):
        self.timer = threading.Timer(self.intervalo, self.enviar)
        self.timer.daemon = True
        self.timer.start()

    def adicionar(self, item):
        with self.lock:
            self.buffer.append(item)
            if len(self.buffer) >= self.tamanho_max:
                logger.info(f"🔄 Lote cheio ({self.tamanho_max}). Enviando...")
                self.enviar(por_tamanho=True)

    def enviar(self, por_tamanho=False):
        with self.lock:
            if self.timer:
                self.timer.cancel()
            if not self.buffer:
                self._agendar()
                return
            dados = list(self.buffer)
            self.buffer.clear()
            self._agendar()

        pacote = {
            "batchId": f"BATCH_{uuid.uuid4().hex[:12]}",
            "sourceNodeId": "GRUPO_1",
            "dataPoints": dados
        }

        origem = "tamanho" if por_tamanho else "tempo"
        if self.fila.mandar(pacote):
            logger.info(f"📤 {len(dados)} itens enviados ({origem})")
        else:
            logger.error(f"❌ Falha no envio. {len(dados)} itens serão persistidos.")
            self.persistir_lote(pacote)

    def persistir_lote(self, pacote):
        with ARQUIVO_LOCK:
            try:
                with open(PENDENTES_PATH, 'r') as f:
                    pendentes = json.load(f)
            except FileNotFoundError:
                logger.warning(f"Arquivo {PENDENTES_PATH} não existe. Criando novo.")
                pendentes = []
            except json.JSONDecodeError:
                logger.warning(f"Erro ao ler JSON em {PENDENTES_PATH}. Sobrescrevendo.")
                pendentes = []

            pendentes.append(pacote)

            with open(PENDENTES_PATH, 'w') as f:
                json.dump(pendentes, f, indent=4)

            logger.info(f"Lote {pacote['batchId']} salvo para reenvio futuro.")

    def desligar(self):
        logger.info("Finalizando EnviadorLote. Enviando o restante...")
        with self.lock:
            if self.timer:
                self.timer.cancel()
            if self.buffer:
                pacote = {
                    "batchId": f"SHUTDOWN_{uuid.uuid4().hex[:12]}",
                    "sourceNodeId": "GRUPO_1",
                    "dataPoints": list(self.buffer)
                }
                self.fila.mandar(pacote)
                logger.info(f"📤 Lote final com {len(self.buffer)} itens enviado.")

class Reenviador:
    def __init__(self, fila, caminho_arquivo, lock, intervalo):
        self.fila = fila
        self.caminho_arquivo = caminho_arquivo
        self.lock = lock
        self.intervalo = intervalo

    def rodar(self):
        logger.info(f"🔄 Reenviador de lotes pendentes iniciado. Verificando a cada {self.intervalo}s.")
        while True:
            time.sleep(self.intervalo)
            
            lotes_pendentes = []
            with self.lock:
                try:
                    if not os.path.exists(self.caminho_arquivo) or os.path.getsize(self.caminho_arquivo) == 0:
                        continue
                    with open(self.caminho_arquivo, 'r') as f:
                        lotes_pendentes = json.load(f)
                    if not isinstance(lotes_pendentes, list) or not lotes_pendentes:
                        continue
                except (FileNotFoundError, json.JSONDecodeError):
                    continue
                
                logger.info(f"🔄 Verificando {len(lotes_pendentes)} lotes pendentes...")
                
                lotes_enviados = []
                for lote in lotes_pendentes:
                    if self.fila.mandar(lote):
                        logger.info(f"📤 Lote pendente {lote.get('batchId', 'N/A')} reenviado com sucesso!")
                        lotes_enviados.append(lote)
                
                if lotes_enviados:
                    lotes_restantes = [l for l in lotes_pendentes if l not in lotes_enviados]
                    with open(self.caminho_arquivo, 'w') as f:
                        json.dump(lotes_restantes, f, indent=4)
                    
                    if not lotes_restantes:
                        logger.info("✅ Fila de lotes pendentes foi limpa com sucesso.")
                    else:
                        logger.info(f"{len(lotes_restantes)} lotes restantes aguardam a próxima tentativa.")

fila = FilaRabbit()
lote = EnviadorLote(fila, MAX_BATCH, INTERVALO_ENVIO)
atexit.register(lote.desligar)

# Inicia o reenviador em uma thread separada
reenviador = Reenviador(fila, PENDENTES_PATH, ARQUIVO_LOCK, INTERVALO_REENVIO)
thread_reenvio = threading.Thread(target=reenviador.rodar, daemon=True)
thread_reenvio.start()

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

def criar_voto(tipo, candidato_nome):
    return {
        "type": tipo,
        "objectIdentifier": candidato_nome,
        "valor": 1,
        "eventDatetime": datetime.now().isoformat()
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
    total_itens_adicionados = 0
    for cidade in resultados:
        votos_por_partido = cidade.get("votos_por_partido", {})
        for partido, votos in votos_por_partido.items():
            for _ in range(votos):
                voto = criar_voto("eleicao", partido)
                lote.adicionar(voto)
                total_itens_adicionados += 1
            logger.info(f"[SIMULAÇÃO] Adicionados {votos} votos para {partido} ao lote.")
    logger.info(f"[SIMULAÇÃO] Total de {total_itens_adicionados} votos adicionados ao processador de lotes.")

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

        # Adiciona o voto ao processador de lotes
        voto = criar_voto(tipo, candidato)
        lote.adicionar(voto)
        
        # Persiste o CPF localmente
        cpfs_votantes.append(cpf)
        with open(arquivo_cpfs, 'w') as f:
            json.dump(cpfs_votantes, f)
        
        return jsonify({"status": "Voto recebido e agendado para envio em lote."}), 200

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
        if fila.ch and fila.ch.is_open:
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
    if fila.ch:
        logger.info("Backend iniciado com conexão ao RabbitMQ estabelecida.")
    else:
        logger.warning("Backend iniciado, mas sem conexão com RabbitMQ. Tentativas de reconexão ocorrerão.")
    
    waitress.serve(app, host='0.0.0.0', port=5001, threads=32)
