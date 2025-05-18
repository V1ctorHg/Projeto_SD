from flask import Flask, jsonify, request
from flask_cors import CORS # type: ignore
import requests
from requests.exceptions import RequestException
import numpy as np
import time
from eleicoesalternativo import eleicao

app = Flask(__name__)
CORS(app)

CORE_URL = "http://127.0.0.1:5001"  # URL do servidor fake (fake_server.py)


#Eleicao alternativa
def espera_resultados(populacao):
    # Base: 0.1 microssegundo por pessoa
    tempo_base = populacao * 0.0001  
    
    # Limita o máximo em 25 segundos para não ficar muito longo
    tempo_maximo = 25000  # 25 segundos em milissegundos
    
    # Usa logaritmo para suavizar o crescimento com populações muito grandes
    tempo_ms = min(tempo_maximo, int(np.log10(populacao + 1) * 1000))
    
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

def enviar_resultados(resultados):
    """
    Envia os resultados da eleição para o servidor.
                
    Args:
        resultados: Lista de dicionários com os resultados de cada cidade
    """
    eleicaoativa = True
    quantidade_cidades = len(resultados)

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

         # Envia este JSON para o servidor Flask
        try:
            core = (f"{CORE_URL}/electionalternative")
            resposta_servidor = requests.post(core, json=json_eleicao, timeout=10)
            resposta_servidor.raise_for_status() # Verifica se houve erro HTTP (4xx ou 5xx)
            print(f"CLIENTE: Iteração {i}: JSON enviado. Servidor respondeu: {resposta_servidor.json().get('message')}")
            serialdaeleicao = resposta_servidor.json().get('serialeleicao')
        except requests.exceptions.RequestException as e:
            print(f"CLIENTE: Iteração {i}: Falha ao enviar JSON para o servidor. Erro: {e}")

        i += 1
        time.sleep(espera_resultados(cidade["populacao"]))

    return jsonify({"message": "Eleição finalizada com sucesso!"})  # Retorna o último estado



@app.route('/candidates', methods=['GET'])
def get_candidates():
    try:
        response = requests.get(f"{CORE_URL}/candidates")
        response.raise_for_status()
        return jsonify(response.json())
    except RequestException as e:
        return jsonify({"error": "Erro ao obter candidatos"}), 500

@app.route('/vote', methods=['POST'])
def send_vote():
    try:
        data = request.json
        if not data or 'cpf' not in data or 'number' not in data:
            return jsonify({"error": "CPF e número do candidato são obrigatórios"}), 400
        
        response = requests.post(f"{CORE_URL}/vote", json=data)
        response.raise_for_status()
        return jsonify(response.json())
    except RequestException as e:
        return jsonify({"error": "Erro ao processar voto"}), 500

@app.route('/results', methods=['GET'])
def get_results():
    try:
        print("\n=== Obtendo resultados do servidor core ===")
        response = requests.get(f"{CORE_URL}/results")
        response.raise_for_status()
        data = response.json()
        print(f"Dados recebidos: {data}")
        print("=== Fim da requisição ===\n")
        return jsonify(data)
    except RequestException as e:
        print(f"Erro ao obter resultados: {e}")
        return jsonify({"error": "Erro ao obter resultados"}), 500

@app.route('/electionalternative', methods =['POST', 'GET'])
def electionalternative():
    if request.method == 'POST':
        data = request.json
        print(f"Dados recebidos: {data}")
        resultados_cidades = eleicao.processar_eleicao(data["num_cidades"], data["partidos"], data["populacao_total"])
        enviar_resultados(resultados_cidades)
        return jsonify({"message": "Dados recebidos com sucesso!"})
    elif request.method == 'GET':

        try:
            # Servidor Local faz a requisição GET para o "Core"
            core = (f"{CORE_URL}/electionalternative")
            print(f"SERVIDOR LOCAL: Buscando dados do Core em {core}...")
            response_from_core = requests.get(core, timeout=10) # timeout de 10 segundos
            response_from_core.raise_for_status() # Verifica se houve erro HTTP (4xx ou 5xx) na resposta do Core

            election_data = response_from_core.json() # Pega o JSON retornado pelo Core
            print("SERVIDOR LOCAL: Dados recebidos do Core com sucesso.")
            
            # Retorna os dados recebidos do Core para o Cliente Angular
            return jsonify(election_data), 200

        except requests.exceptions.Timeout:
            print("SERVIDOR LOCAL: Timeout ao tentar contatar o Core.")
            return jsonify({"error": "Serviço principal (Core) demorou a responder."}), 504 # Gateway Timeout
        except requests.exceptions.ConnectionError:
            print("SERVIDOR LOCAL: Não foi possível conectar ao Core.")
            return jsonify({"error": "Falha ao conectar com o serviço principal (Core)."}), 503 # Service Unavailable
        except requests.exceptions.HTTPError as e:
            # Se o Core retornou um erro HTTP (ex: 404, 500)
            print(f"SERVIDOR LOCAL: O Core retornou um erro HTTP: {e.response.status_code}")
            try:
                # Tenta repassar a mensagem de erro do Core
                return jsonify(e.response.json()), e.response.status_code
            except ValueError: # Se a resposta de erro do Core não for JSON
                return jsonify({"error": f"Erro do serviço Core ({e.response.status_code})"}), 502 # Bad Gateway
        except Exception as e:
            # Qualquer outro erro
            print(f"SERVIDOR LOCAL: Erro inesperado: {str(e)}")
            return jsonify({"error": f"Erro interno no servidor local: {str(e)}"}), 500
    
@app.route('/')
def index():
    return jsonify({"message": "API de votação rodando!"})

if __name__ == "__main__":
    app.run(port=5000, debug=True)
