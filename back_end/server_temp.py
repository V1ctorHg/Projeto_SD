from flask import Flask, jsonify, request
import json
import os

app = Flask(__name__)

DATA_PATH = os.path.join(os.path.dirname(__file__), "Data")
CANDIDATES_FILE = os.path.join(DATA_PATH, "candidates.json")
VOTES_FILE = os.path.join(DATA_PATH, "votes.json")

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
        # Carregar dados
        votes = load_data(VOTES_FILE)
        candidates = load_data(CANDIDATES_FILE)
        
        print("\n=== DEBUG RESULTADOS ===")
        print(f"Votos carregados: {votes}")
        print(f"Candidatos carregados: {candidates}")
        
        # Inicializar resultados com informações dos candidatos
        results = {}
        for candidate in candidates:
            candidate_number = str(candidate["number"])
            results[candidate_number] = {
                "name": candidate["name"],
                "number": candidate["number"],
                "party": candidate["party"],
                "votes": 0
            }
        
        # Contar votos
        for vote in votes:
            candidate_number = str(vote["number"])
            if candidate_number in results:
                results[candidate_number]["votes"] += 1
        
        print(f"Resultados finais: {results}")
        print("=== FIM DEBUG ===\n")
        
        return jsonify(results)
    except Exception as e:
        print(f"Erro ao processar resultados: {e}")
        return jsonify({"error": str(e)}), 500

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
