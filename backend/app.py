from flask import Flask, jsonify, request
from flask_cors import CORS # type: ignore
import waitress
import requests
import threading
from requests.exceptions import RequestException
import time
import os
from eleicoesalternativo import eleicao
from datetime import datetime, timedelta
import logging
from dateutil import parser
from kafka import KafkaProducer, KafkaConsumer
import json
import random
import sys



app = Flask(__name__)
CORS(app)

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


##CORE_URL = "http://localhost:5000"  # Rodar local
CORE_URL = "http://host.docker.internal:5000"  # Rodar para o docker
CACHE_DURACAO = 30  # segundos

MAX_TENTATIVAS = 5
DELAY_RETENTATIVA = 5


BUFFER_VOTOS = []
LOCK = threading.Lock() #seção crítica

MAX_BUFFER = 500 #max de votos no buffer
INTERVALO_ENVIO = 2 #max de segundos

def adicionar_voto_buffer(voto):
    with LOCK:
        BUFFER_VOTOS.append(voto)
        logger.info(f"{BUFFER_VOTOS}")
        if len(BUFFER_VOTOS) >= MAX_BUFFER:
            logger.info("Lote cheio, eviando imediatamente")
            enviar_lote()


def enviar_lote():
    global BUFFER_VOTOS
    with LOCK:
        if not BUFFER_VOTOS:
            return
        lote = BUFFER_VOTOS.copy()
        BUFFER_VOTOS.clear()
        logger.info(f"Enviando lote de {len(lote)} votos para o core")

    # Processar em paralelo para acelerar
    def enviar_voto_individual(voto):
        try:
            response = requests.post(f"{CORE_URL}/votar", json=voto)
            response.raise_for_status()
            logger.debug(f"Voto enviado: {voto['cpf']}")
        except Exception as e:
            logger.error(f"Erro ao enviar voto: {e}")
            # Re-adiciona ao buffer em caso de erro
            with LOCK:
                BUFFER_VOTOS.append(voto)

    # Criar threads para enviar votos em paralelo
    threads = []
    for voto in lote:
        thread = threading.Thread(target=enviar_voto_individual, args=(voto,))
        threads.append(thread)
        thread.start()
        
        # Limitar a 50 threads simultâneas para não sobrecarregar
        if len(threads) >= 50:
            for t in threads:
                t.join()
            threads = []
    
    # Aguardar threads restantes
    for thread in threads:
        thread.join()
    
    logger.info(f"Lote de {len(lote)} votos processado com sucesso")

def iniciar_envio_periodico():
    def loop():
        while True:
            time.sleep(INTERVALO_ENVIO)
            enviar_lote()
    threading.Thread(target=loop, daemon=True).start()

iniciar_envio_periodico() #enviando um lote a cada 2 seg


producer = KafkaProducer(
    bootstrap_servers=os.getenv("KAFKA_BROKER", "localhost:9092"),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)


def consumidor_loop():
    consumer = KafkaConsumer(
        'votos',
        bootstrap_servers=os.getenv("KAFKA_BROKER", "localhost:9092"),
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        max_poll_records=500,  # Consumir até 500 mensagens por vez
        fetch_max_wait_ms=100  # Reduzir tempo de espera
    )

    ultimo_envio = time.time()

    for mensagem in consumer:
        voto = mensagem.value
        logger.debug(f"Voto consumido do Kafka: {voto['cpf']}")  # Mudei para debug para reduzir logs

        with LOCK:
            BUFFER_VOTOS.append(voto)

        agora = time.time()
        tempo_passado = agora - ultimo_envio
        buffer_cheio = len(BUFFER_VOTOS) >= MAX_BUFFER
        tempo_excedido = tempo_passado >= INTERVALO_ENVIO

        if buffer_cheio or tempo_excedido:
            logger.info(f"Enviando lote: {len(BUFFER_VOTOS)} votos (motivo: {'buffer cheio' if buffer_cheio else 'tempo excedido'})")
            enviar_lote()
            ultimo_envio = time.time()



threading.Thread(target=consumidor_loop, daemon=True).start()


# Cache de resultados
resultados_cache = {
    "timestamp": None,
    "dados": None
}


def processar_eleicao(data):
            #try except aqui depois
            response = requests.get(f"{CORE_URL}/candidatos")
            response.raise_for_status()
            logger.info(f"CLIENTE: Dados recebidos: {response.json()}")

            candidatos = [candidato['id'] for candidato in response.json()]
            logger.info(f"CLIENTE: Candidatos: {candidatos}")

            resultados_cidades = eleicao.processar_eleicao(data["num_cidades"], candidatos, data["populacao_total"])
            enviar_resultados(resultados_cidades)

def enviar_resultados(resultados):
    i = 0
    total_votos_enviados = 0

    for cidade in resultados:
        jsonparcial = {
            "votos_por_partido": cidade["votos_por_partido"]
        }
        
        for partido, votos in jsonparcial["votos_por_partido"].items():
            for _ in range(votos):  
                cpf = f"{random.randint(0, 99999999999):011d}"
                json_eleicao = {
                    "cpf": cpf,
                    "candidato_id": partido
                }
                
                producer.send("votos", json_eleicao)
                total_votos_enviados += 1
            
            logger.info(f"Enviados {votos} votos para o partido {partido}")

        i += 1
    
    logger.info(f"Total de votos enviados: {total_votos_enviados}")


@app.route('/votar', methods=['POST'])
def votar(dados=None):
    try:
        if not dados:
            dados = request.json
        cpf = dados.get('cpf')
        candidato_id = dados.get('candidato_id')

        valido, mensagem = validar_voto(cpf, candidato_id)
        if not valido:
            return jsonify({"erro": mensagem}), 400

        producer.send("votos", {"cpf": cpf, "candidato_id": candidato_id})
        return jsonify({"status": "Voto enviado para fila Kafka"}), 200

    except Exception as e:
        logger.info(f"Erro ao processar voto: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500
    

@app.route('/candidatos', methods=['GET'])
def getCandidates():
    """
    Endpoint para listar candidatos
    """
    try:
        logger.info("Backend: Recebendo requisição GET /candidatos")
        response = requests.get(f"{CORE_URL}/candidatos")
        logger.info(f"Backend: Resposta do SD_core: {response.status_code}")
        logger.info(f"Backend: Dados recebidos: {response.json()}")
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        logger.info(f"Backend: Erro de conexão com SD_core: {str(e)}")
        logger.info(f"Erro ao listar candidatos: {str(e)}")
        return jsonify({"erro": "Erro ao conectar com o servidor central"}), 500
    except Exception as e:
        logger.info(f"Backend: Erro ao listar candidatos: {str(e)}")
        logger.info(f"Erro ao listar candidatos: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500
    
@app.route('/resultados', methods=['GET'])
def resultados():
    """
    Endpoint para obter resultados com cache
    """
    try:
        # Verifica se o cache está válido
        agora = datetime.now()
        if (resultados_cache["timestamp"] and 
            agora - resultados_cache["timestamp"] < timedelta(seconds=CACHE_DURACAO)):
            return jsonify(resultados_cache["dados"])
            
        # Se não estiver válido, busca do servidor central
        response = requests.get(f"{CORE_URL}/resultados")
        if response.status_code == 200:
            resultados_cache["dados"] = response.json()
            resultados_cache["timestamp"] = agora
            return jsonify(resultados_cache["dados"])
        else:
            return jsonify({"erro": "Erro ao buscar resultados"}), 500
            
    except Exception as e:
        logger.info(f"Erro ao buscar resultados: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500


#Quando for fazer a simulação de eleição com muitos votos, integrar à rota \votar
@app.route('/electionalternative', methods =['POST', 'GET'])
def electionalternative():
    if request.method == 'POST':
        data = request.json
        logger.info(f"Dados recebidos: {data}")
        threading.Thread(target=processar_eleicao, args=(data,), daemon=True).start()
        return jsonify({"message": "Parte da eleição colocada na fila"})
    
@app.route('/')
def index():
    return jsonify({"message": "API de votação rodando!"})

def validar_voto(cpf, candidato_id):
    """
    Implementa validações adicionais antes de enviar para o servidor central
    """
    # Validações básicas
    if not cpf or not candidato_id:
        return False, "CPF e ID do candidato são obrigatórios"
    
    # Validação de CPF já votou
    try:
        response = requests.get(f"{CORE_URL}/eleitor/{cpf}")
        if response.status_code == 200:
            eleitor = response.json()
            if eleitor.get('votou'):
                return False, "CPF já votou"
    except Exception as e:
        logger.info(f"Erro ao verificar CPF: {str(e)}")
        # Em caso de erro na verificação, permite o voto seguir para o servidor central
        # que fará a validação final
    
    return True, None



@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    """
    Endpoint para cadastro de eleitores
    """
    try:
        response = requests.post(
            f"{CORE_URL}/cadastrar",
            json=request.json
        )
        return response.json(), response.status_code
    except Exception as e:
        logger.info(f"Erro ao cadastrar eleitor: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500



@app.route('/eleitor/<cpf>', methods=['GET'])
def verificar_eleitor(cpf):
    """
    Endpoint para verificar status do eleitor
    """
    try:
        response = requests.get(f"{CORE_URL}/eleitor/{cpf}")
        return response.json(), response.status_code
    except Exception as e:
        logger.info(f"Erro ao verificar eleitor: {str(e)}")
        return jsonify({"erro": "Erro ao verificar eleitor"}), 500

if __name__ == "__main__":
    waitress.serve(app, host='0.0.0.0', port=5001, threads=32)
