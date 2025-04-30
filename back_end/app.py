from flask import Flask, request, jsonify
import requests
from config import AGREGADOR_URL

app = Flask(__name__)

@app.route('/votar', methods=['POST'])
def votar():
    dados = request.get_json()
    try:
        response = requests.post(f'{AGREGADOR_URL}/receber-voto', json=dados)
        return jsonify({'status': 'enviado', 'resposta': response.json()}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'status': 'erro', 'detalhe': str(e)}), 500

@app.route('/resultados', methods=['GET'])
def resultados():
    try:
        response = requests.get(f'{AGREGADOR_URL}/resultados')
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'status': 'erro', 'detalhe': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)