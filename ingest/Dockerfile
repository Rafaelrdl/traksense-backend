# ============================================================================
# Dockerfile - TrakSense Ingest Service
# ============================================================================
# Cria imagem Docker otimizada para o serviço de ingestão de dados IoT.
#
# Características:
# - Imagem base slim (menor tamanho, menor superfície de ataque)
# - Multi-stage build não necessário (serviço simples)
# - Sem cache de pip (reduz tamanho da imagem)
# - User não-root será adicionado na Fase 2 (segurança)
#
# Build:
#   docker build -t traksense-ingest:latest -f ingest/Dockerfile ingest/
#
# Run (standalone):
#   docker run -e MQTT_URL=mqtt://emqx:1883 traksense-ingest:latest
#
# Produção:
#   Use docker-compose.yml em infra/ para orquestração completa
# ============================================================================

# ----------------------------------------------------------------------------
# Base: Python 3.12 Slim
# ----------------------------------------------------------------------------
# python:3.12-slim: Imagem oficial Python sem pacotes desnecessários
# - Baseada em Debian Bookworm
# - ~120MB vs ~900MB da imagem full
# - Contém apenas runtime Python essencial
# - Compatível com asyncio e bibliotecas modernas
FROM python:3.12-slim

# ----------------------------------------------------------------------------
# Configuração do Ambiente
# ----------------------------------------------------------------------------
# Define diretório de trabalho dentro do container
# Todos os comandos subsequentes executam a partir de /app
WORKDIR /app

# ----------------------------------------------------------------------------
# Instalação de Dependências
# ----------------------------------------------------------------------------
# Copia requirements.txt ANTES do código fonte
# Benefício: Layer de dependências é cacheado se requirements.txt não mudar
# Rebuild é mais rápido quando apenas código Python muda
COPY requirements.txt .

# Instala dependências Python
# --no-cache-dir: Não armazena cache do pip (reduz tamanho da imagem)
# -r requirements.txt: Lê dependências do arquivo
# Instala: aiomqtt, asyncpg, pydantic
RUN pip install --no-cache-dir -r requirements.txt

# ----------------------------------------------------------------------------
# Cópia do Código Fonte
# ----------------------------------------------------------------------------
# Copia todo o código fonte para /app
# Inclui:
# - main.py (ponto de entrada)
# - adapters/ (normalização de payloads)
# Exclui:
# - Arquivos listados em .dockerignore (cache, .git, etc.)
COPY . .

# ----------------------------------------------------------------------------
# Comando de Execução
# ----------------------------------------------------------------------------
# CMD: Comando padrão executado quando container inicia
# Formato exec (lista): Mais eficiente, sinais UNIX funcionam corretamente
# Executa: python main.py
#
# Nota: Em produção, considere usar:
# - Restart policy: --restart=unless-stopped
# - Health check: HEALTHCHECK CMD python -c "import socket; ..."
# - Limites de recursos: --memory=512m --cpus=1
CMD ["python", "main.py"]

# ============================================================================
# MELHORIAS FUTURAS (Fase 2+)
# ============================================================================
# 1. Multi-stage build para imagem ainda menor
# 2. User não-root para segurança:
#    RUN useradd -m -u 1000 ingest && chown -R ingest:ingest /app
#    USER ingest
# 3. Health check integrado:
#    HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
#      CMD python -c "import asyncio, aiomqtt; ..."
# 4. Labels para metadata:
#    LABEL maintainer="traksense@example.com"
#    LABEL version="1.0.0"
# 5. Volume para logs persistentes:
#    VOLUME ["/app/logs"]
# ============================================================================
