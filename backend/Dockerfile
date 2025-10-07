# ============================================================================
# Dockerfile - TrakSense Backend API (Django)
# ============================================================================
# Cria imagem Docker otimizada para o backend Django com suporte a
# PostgreSQL/TimescaleDB, django-tenants e Django REST Framework.
#
# Build:
#   docker build -t traksense-api:latest -f backend/Dockerfile backend/
#
# Produção:
#   Use docker-compose.yml em infra/ para orquestração completa
# ============================================================================

# Base: Python 3.12 Slim (~120MB vs ~900MB da imagem full)
FROM python:3.12-slim

# Define /app como diretório de trabalho
WORKDIR /app

# Variáveis de ambiente para otimizar Python em container:
# - PYTHONDONTWRITEBYTECODE=1: Não gera arquivos .pyc
# - PYTHONUNBUFFERED=1: Saída Python sem buffer (logs imediatos)
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Instala ferramentas necessárias para compilar psycopg2:
# - build-essential: Compiladores C/C++ (gcc, g++, make)
# - libpq-dev: Headers PostgreSQL (necessário para psycopg2)
# Remove cache do apt para reduzir tamanho da imagem
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Copia requirements.txt ANTES do código fonte
# Benefício: Layer de dependências é cacheado se requirements.txt não mudar
COPY requirements.txt .

# Instala dependências Python
# --no-cache-dir: Não armazena cache do pip (reduz tamanho ~50MB)
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código fonte Django para /app
# Inclui: manage.py, core/, apps/, health/, tests/
# Exclui: Arquivos listados em .dockerignore
COPY . .

# Expõe porta 8000 para comunicação HTTP
# Django development server roda nesta porta por padrão
EXPOSE 8000

# CMD definido no docker-compose.yml:
# 1. python manage.py migrate_schemas (migrações)
# 2. python manage.py runserver 0.0.0.0:8000 (inicia servidor)
