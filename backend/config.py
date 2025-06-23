#AGREGADOR_URL = 'http://127.0.0.1:8000'
AGREGADOR_URL = "http://agregador:8000" #para rodar no docker

import os

# Configurações de autenticação
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin')

# Configuração JWT
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'j41ub4W2445fF54f545I4U5vTVYVhghy342vy')
JWT_ACCESS_TOKEN_EXPIRES = 600
