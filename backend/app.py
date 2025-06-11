from flask import Flask, jsonify, request
from flask_cors import CORS # type: ignore
import waitress
import requests
import threading
from queue import Queue
from requests.exceptions import RequestException
import numpy as np
import time
import os
from eleicoesalternativo import eleicao
from datetime import datetime, timedelta
import logging
from dateutil import parser

app = Flask(__name__)
CORS(app)

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


#CORE_URL = os.getenv("CORE_URL", "http://pseudo-core:5001")  #para rodar no docker


##CORE_URL = "http://localhost:5000"  # Rodar local
CORE_URL = "http://host.docker.internal:5000"  # Rodar para o docker
CACHE_DURACAO = 30  # segundos

MAX_TENTATIVAS = 5
DELAY_RETENTATIVA = 5

#Fila de mensagens (só para as eleições)
fila_eleicoes = Queue()

# Fila de votos
voto_queue = Queue()
processando_fila = False

# Cache de resultados
resultados_cache = {
    "timestamp": None,
    "dados": None
}

# Thread para processar as eleições
def worker():
    while True:
        data = fila_eleicoes.get()
        print(f"Fila de eleições: {fila_eleicoes}")
        if data is None:
            break
        processar_eleicao(data)
        fila_eleicoes.task_done()

threading.Thread(target=worker, daemon=True).start()

#Eleicao alternativa
def espera_resultados(populacao):
    # Base: 0.1 microssegundo por pessoa
    tempo_base = populacao * 0.0001  
    
    # Limita o máximo em 25 segundos para não ficar muito longo
    tempo_maximo = 25000  # 25 segundos em milissegundos
    
    # Usa logaritmo para suavizar o crescimento com populações muito grandes
    tempo_ms = min(tempo_maximo, tempo_base)
    
    return tempo_ms/1000  # retorna em segundos

def eleicao_matematicamente_definida(votos_por_partido_atuais, populacao_total_da_eleicao, total_eleitores_ja_processados):
    """
    Verifica se a eleição está matematicamente definida, considerando que todos os 
    eleitores ainda não processados votariam no segundo colocado.

    Args:
        votos_por_partido_atuais (dict): Dicionário com os votos atuais de cada partido.
        populacao_total_da_eleicao (int): Número total de eleitores aptos na eleição.
        total_eleitores_ja_processados (int): Soma dos eleitores das áreas já apuradas.

    Returns:
        tuple: (bool, str or None) indicando (True se definida, nome do vencedor) 
            ou (False se não definida, None).
    """

    if not votos_por_partido_atuais:
        return False, None # Não há dados de votos

    # Calcula os eleitores restantes que ainda podem, hipoteticamente, votar.
    eleitores_potenciais_restantes = populacao_total_da_eleicao - total_eleitores_ja_processados
    
    # Garante que não seja negativo (caso total_eleitores_ja_processados exceda por algum motivo)
    if eleitores_potenciais_restantes < 0:
        eleitores_potenciais_restantes = 0

    # Ordena para pegar líder e segundo
    partidos_ordenados = sorted(votos_por_partido_atuais.items(), key=lambda item: item[1], reverse=True)
    
    lider_atual_nome, votos_lider_atual = partidos_ordenados[0]

    # Se só tem um partido na lista (ou com votos)
    if len(partidos_ordenados) == 1:
        # Ele ganha se seus votos superam os eleitores restantes 
        # (considerando que esses eleitores poderiam formar um novo partido e votar nele),
        # ou se não há mais eleitores restantes.
        if votos_lider_atual > eleitores_potenciais_restantes or eleitores_potenciais_restantes == 0:
            return True, lider_atual_nome
        return False, None # Ainda pode ser ultrapassado por um "novo" concorrente com os eleitores restantes

    # Se tem mais de um, pega o segundo colocado
    _, votos_segundo_colocado = partidos_ordenados[1]
    
    diferenca_para_segundo = votos_lider_atual - votos_segundo_colocado
    
    # Se a diferença já é maior que todos os eleitores que faltam ser processados
    # (assumindo que todos eles votariam no segundo colocado), está definido.
    if diferenca_para_segundo > eleitores_potenciais_restantes:
        return True, lider_atual_nome
        
    return False, None # Caso contrário, não está definido  


def processar_eleicao(data):
            response = requests.get(f"{CORE_URL}/candidatos")
            response.raise_for_status()
            print(f"CLIENTE: Dados recebidos: {response.json()}")

            candidatos = [candidato['numero'] for candidato in response.json()]
            print(f"CLIENTE: Candidatos: {candidatos}")

            resultados_cidades = eleicao.processar_eleicao(data["num_cidades"], candidatos, data["populacao_total"])
            enviar_resultados(resultados_cidades)

def enviar_resultados(resultados):
    """
    Envia os resultados da eleição para o servidor.
                
    Args:
        resultados: Lista de dicionários com os resultados de cada cidade
    """
    eleicaoativa = True

    totalpopulacao = 0
    totalvotos = 0
    votos_por_partido = {}
    serialdaeleicao = None
    i = 0

    for cidade in resultados:
    
        jsonparcial = {
            "total_populacao": cidade["populacao"],
            "total_votos": cidade["total_votos"],
            "votos_por_partido": cidade["votos_por_partido"],
            "eleicaoativa": eleicaoativa
        }
        
        totalpopulacao += jsonparcial["total_populacao"]
        totalvotos += jsonparcial["total_votos"]
        
        for partido, votos in jsonparcial["votos_por_partido"].items():
            votos_por_partido[partido] = votos_por_partido.get(partido, 0) + votos
        ativaeleicao = jsonparcial["eleicaoativa"]
        if totalpopulacao == cidade["totalpossiveiseleitores"]:
            ativaeleicao = False
       

        json_eleicao = {
            "electionpart": i,
            "serialeleicao": serialdaeleicao,
            "totalpopulacao": totalpopulacao,
            "totalvotos": totalvotos,
            "votos_por_partido": votos_por_partido,
            "ativaeleicao": ativaeleicao,
            "totalpossiveiseleitores": cidade["totalpossiveiseleitores"],
            #depois colocar aqui o usuário que solicitou a eleição e o timestamp
        }

         # Envia este JSON para o servidor Flask, tentando até MAX_TENTATIVAS vezes
        for tentativa in range(MAX_TENTATIVAS):
            try:
                core = (f"{CORE_URL}/electionalternative")
                resposta_servidor = requests.post(core, json=json_eleicao, timeout=10)
                resposta_servidor.raise_for_status() # Verifica se houve erro HTTP (4xx ou 5xx)
                print(f"CLIENTE: Iteração {i}: JSON enviado. Servidor respondeu: {resposta_servidor.json().get('message')}")
                serialdaeleicao = resposta_servidor.json().get('serialeleicao')
                #time.sleep(0.2)
                break
            except requests.exceptions.RequestException as e:
                print(f"CLIENTE: Iteração {i}: Falha ao enviar JSON para o servidor. Erro: {e}")
                if tentativa < MAX_TENTATIVAS - 1:
                    time.sleep(DELAY_RETENTATIVA)
                else:
                    print(f"CLIENTE: Iteração {i}: Falha após {MAX_TENTATIVAS} tentativas. Retornando erro.")
                    return jsonify({"error": "Erro ao enviar dados para o servidor"}), 500

        i += 1
        time.sleep(espera_resultados(cidade["populacao"]))

    return 

@app.route('/votar', methods=['POST'])
def votar():
    """
    Endpoint para registro de votos com validação e fila
    """
    try:
        dados = request.json
        cpf = dados.get('cpf')
        candidato_id = dados.get('candidato_id')
        
        # Validação local
        valido, mensagem = validar_voto(cpf, candidato_id)
        if not valido:
            return jsonify({"erro": mensagem}), 400
        
        # Envia para o servidor central
        response = requests.post(
            f"{CORE_URL}/votar",
            json={"cpf": cpf, "candidato_id": candidato_id}
        )
        
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify(response.json()), response.status_code
            
    except Exception as e:
        logger.error(f"Erro ao processar voto: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500

@app.route('/candidatos', methods=['GET'])
def getCandidates():
    """
    Endpoint para listar candidatos
    """
    try:
        print("Backend: Recebendo requisição GET /candidatos")
        response = requests.get(f"{CORE_URL}/candidatos")
        print(f"Backend: Resposta do SD_core: {response.status_code}")
        print(f"Backend: Dados recebidos: {response.json()}")
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        print(f"Backend: Erro de conexão com SD_core: {str(e)}")
        logger.error(f"Erro ao listar candidatos: {str(e)}")
        return jsonify({"erro": "Erro ao conectar com o servidor central"}), 500
    except Exception as e:
        print(f"Backend: Erro ao listar candidatos: {str(e)}")
        logger.error(f"Erro ao listar candidatos: {str(e)}")
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
        logger.error(f"Erro ao buscar resultados: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500

@app.route('/electionalternative', methods =['POST'])
def electionalternative():
    if request.method == 'POST':
        data = request.json
        print(f"Dados recebidos: {data}")

        fila_eleicoes.put(data)
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
        logger.error(f"Erro ao verificar CPF: {str(e)}")
        # Em caso de erro na verificação, permite o voto seguir para o servidor central
        # que fará a validação final
    
    return True, None

def processar_fila():
    """
    Processa a fila de votos em background
    """
    global processando_fila
    
    while True:
        if not voto_queue.empty():
            try:
                voto = voto_queue.get()
                # Tenta enviar para o servidor central
                response = requests.post(
                    f"{CORE_URL}/votar",
                    json=voto
                )
                
                if response.status_code == 200:
                    logger.info(f"Voto processado com sucesso: {voto}")
                else:
                    # Se falhar, coloca de volta na fila
                    voto_queue.put(voto)
                    logger.error(f"Erro ao processar voto: {response.text}")
                
            except Exception as e:
                logger.error(f"Erro ao processar voto: {str(e)}")
                # Coloca de volta na fila em caso de erro
                voto_queue.put(voto)
        
        time.sleep(1)  # Evita consumo excessivo de CPU

# Inicia o processamento da fila em background
threading.Thread(target=processar_fila, daemon=True).start()


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
        logger.error(f"Erro ao cadastrar eleitor: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500

@app.route('/electionalternative', methods=['POST'])
def election_alternative():
    """
    Endpoint para configuração alternativa de eleição
    """
    try:
        response = requests.post(
            f"{CORE_URL}/electionalternative",
            json=request.json
        )
        return response.json(), response.status_code
    except Exception as e:
        logger.error(f"Erro ao configurar eleição alternativa: {str(e)}")
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
        logger.error(f"Erro ao verificar eleitor: {str(e)}")
        return jsonify({"erro": "Erro ao verificar eleitor"}), 500

if __name__ == "__main__":
    waitress.serve(app, host='0.0.0.0', port=5001, threads=32)
