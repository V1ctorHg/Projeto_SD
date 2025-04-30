# 🗳️ Sistema de Votação Distribuído

Este projeto simula um sistema de votação distribuído, com múltiplos nós coletores (clientes) que enviam dados para um nó agregador (servidor central). O foco deste repositório está no desenvolvimento da **interface de votação (front-end)** e do **cliente back-end responsável por comunicar-se com o servidor central**.

---

## 📁 Estrutura do Projeto

```
/
├── front-end/      # Interface do usuário em Angular
└── back-end/       # Cliente Flask que envia dados ao agregador
```


---

## 🔧 Pré-requisitos

- Node.js (v16+)
- Angular CLI (`npm install -g @angular/cli`)
- Python 3.8+
- `pip` instalado

---

## 🖥️ Front-end (Angular)

### 📦 Instalação

```bash
cd front-end/
npm install
```

### 🚀 Execução

```bash
ng serve
```

Acesse no navegador:

```
http://localhost:4200
```

### 🔄 Atualizar o projeto com mudanças do Git

```bash
git pull
```

---

## 🧠 Back-end (Flask - Cliente)

### 📦 Criar e ativar ambiente virtual

```bash
cd back-end/
python -m venv venv
```

#### ▶️ Ative o ambiente virtual:

**Windows (CMD ou PowerShell):**

```bash
venv\Scripts\activate
```

**Linux/macOS:**

```bash
source venv/bin/activate
```

### 🔧 Instalar as dependências

```bash
pip install -r requirements.txt
```

> Se ainda não existir o `requirements.txt`, após instalar os pacotes com `pip install flask`, execute:

```bash
pip freeze > requirements.txt
```

### 🚀 Executar o back-end

```bash
python app.py
```

---

## 📦 Reinstalar dependências (após atualizações)

Se outro membro do time adicionar novas bibliotecas, você pode atualizar desse jeito:

```bash
pip install -r requirements.txt
```

---

## 📁 Arquivos ignorados pelo Git

O repositório ignora arquivos que não devem ser versionados:

```
# Arquivos comuns no .gitignore:

# Angular
node_modules/
dist/

# Python
venv/
__pycache__/
*.pyc
```

---

## 🧑‍💻 Contribuição e Clonagem

### Para clonar o repositório:

```bash
git clone https://github.com/SEU_USUARIO/NOME_DO_REPOSITORIO.git
```

Depois entre nas pastas:

```bash
cd front-end/     # ou cd back-end/
```

---

## ✅ O que o projeto faz

- Interface para votação com Angular.
- Envio de votos/dados para um servidor agregador (externo).
- Comunicação por JSON via HTTP.
- Simulação de um nó coletor do sistema distribuído.

---

## ✍️ Observações Finais

- O servidor central (Core) **não está incluído neste repositório**.
- O foco aqui são os nós clientes.
- Qualquer dúvida sobre execução, abra uma issue ou fale com o grupo.

---