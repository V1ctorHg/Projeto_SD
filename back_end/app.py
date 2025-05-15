from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from requests.exceptions import RequestException

app = Flask(__name__)
CORS(app)

CORE_URL = "http://127.0.0.1:5001"  # URL do servidor fake (fake_server.py)

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

@app.route('/')
def index():
    return jsonify({"message": "API de votação rodando!"})

if __name__ == "__main__":
    app.run(port=5000, debug=True)
