from flask import Flask, jsonify, request
from flask_cors import CORS # type: ignore
import json
import os
import time
import numpy as np
from eleicoesalternativo import eleicao

app = Flask(__name__)
CORS(app)

DATA_PATH = os.path.join(os.path.dirname(__file__), "Data")
CANDIDATES_FILE = os.path.join(DATA_PATH, "candidates.json")
VOTES_FILE = os.path.join(DATA_PATH, "votes.json")
SERIAL_VOTES_FILE = os.path.join(DATA_PATH, "serial_votes.json")

ELECTION_FILE = os.path.join(DATA_PATH, "election.json")

def load_data(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except Exception as e:
        print(f"Erro ao ler arquivo {file_path}: {e}")
        return []

def save_data(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)
    
    return True

@app.route('/candidates', methods=['GET'])
def get_candidates():
    candidates = load_data(CANDIDATES_FILE)
    return jsonify(candidates)

@app.route('/')
def index():
    return jsonify({"message": "Servidor core rodando!"})

@app.route('/vote', methods=['POST'])
def register_vote():
    try:
        data = request.json
        cpf = data.get("cpf")
        candidate_number = data.get("number")

        if not cpf or not cpf.isdigit() or len(cpf) != 11:
            return jsonify({"error": "CPF inválido"}), 400

        votes = load_data(VOTES_FILE)
        candidates = load_data(CANDIDATES_FILE)

        # Verificar se CPF já votou
        for vote in votes:
            if vote["cpf"] == cpf:
                return jsonify({"error": "CPF já votou!"}), 400

        # Verificar se candidato existe
        if not any(c["number"] == candidate_number for c in candidates):
            return jsonify({"error": "Candidato não encontrado!"}), 400

        # Registrar voto
        votes.append(data)
        save_data(VOTES_FILE, votes)

        return jsonify({"message": "Voto registrado com sucesso!"})
    except Exception as e:
        print(f"Erro ao processar voto: {e}")
        return jsonify({"error": "Erro ao processar voto"}), 500

@app.route('/results', methods=['GET'])
def get_results():
    try:
        # Carregar dados principais
        votes = load_data(VOTES_FILE)
        candidates = load_data(CANDIDATES_FILE)
        election_data = load_data(ELECTION_FILE)

        #O que estava aqui agora esta no cliente
        
        data ={"votes": votes, "candidates": candidates, "election_data": election_data}

        return jsonify(data)

    except Exception as e:
        print(f"Erro ao processar resultados: {e}")
        return jsonify({"error": str(e)}), 500


#Para o alternativo
@app.route('/electionalternative', methods=['POST'])
def electionalternative():
    if not request.is_json:
        return jsonify({"error": "A requisição deve ser JSON"}), 400

    json_para_salvar = request.json
    print(f"Recebido JSON do cliente para salvar: {json_para_salvar}")

    part = json_para_salvar.get("electionpart")
    if part is None:
        return jsonify({"error": "Faltando electionpart no JSON"}), 400

    # Gera ou recupera o serial da eleição
    if part == 0:
        try:
            with open(SERIAL_VOTES_FILE, "r") as file:
                serial = json.load(file)
                serial_eleicao = serial.get("serial", 0)
        except FileNotFoundError:
            serial_eleicao = 0

        json_para_salvar["serialeleicao"] = serial_eleicao
        novo_serial = serial_eleicao + 1
        save_data(SERIAL_VOTES_FILE, {"serial": novo_serial})
    else:
        serial_eleicao = json_para_salvar.get("serialeleicao")

    # Carrega todas as eleições
    try:
        with open(ELECTION_FILE, "r") as file:
            dados_eleicoes = json.load(file)
    except FileNotFoundError:
        dados_eleicoes = {}

    # Salva ou sobrescreve toda a eleição correspondente
    serial_str = str(serial_eleicao)
    dados_eleicoes[serial_str] = {
        "serialeleicao": serial_eleicao,
        "electionpart": part,
        "totalpopulacao": json_para_salvar.get("totalpopulacao"),
        "totalvotos": json_para_salvar.get("totalvotos"),
        "votos_por_partido": json_para_salvar.get("votos_por_partido", {}),
        "ativaeleicao": json_para_salvar.get("ativaeleicao"),
        "totalpossiveiseleitores": json_para_salvar.get("totalpossiveiseleitores")
    }

    if save_data(ELECTION_FILE, dados_eleicoes):
        print("Eleição salva (sobrescrita) com sucesso!")
        return jsonify({"message": "Eleição salva!", "serialeleicao": serial_eleicao}), 200
    else:
        print("Erro ao salvar a eleição.")
        return jsonify({"error": "Erro ao salvar a eleição."}), 500



if __name__ == "__main__":
    os.makedirs(DATA_PATH, exist_ok=True)
    
    # Cria arquivos iniciais se não existirem
    if not os.path.exists(CANDIDATES_FILE):
        initial_candidates = [
            {"number": 1, "name": "Candidato A", "party": "Partido X"},
            {"number": 2, "name": "Candidato B", "party": "Partido Y"}
        ]
        save_data(CANDIDATES_FILE, initial_candidates)
        print(f"Arquivo de candidatos criado: {initial_candidates}")

    if not os.path.exists(VOTES_FILE):
        save_data(VOTES_FILE, [])
        print("Arquivo de votos vazio criado")

    print(f"Servidor iniciado na porta 5001")
    print(f"Diretório de dados: {DATA_PATH}")
    app.run(port=5001, debug=True)
