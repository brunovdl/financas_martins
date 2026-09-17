# ============================================================
# MAI Finance Flet Web App — Dockerfile Multi-Stage
# ============================================================

# Stage 1: Builder — instala dependências em ambiente isolado
FROM python:3.11-slim AS builder

WORKDIR /app

# Instala dependências de build do sistema se necessário
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================================
# Stage 2: Runner — imagem final de produção enxuta e segura
# ============================================================
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/appuser/.local/bin:$PATH \
    FLET_PORT=8550 \
    PORT=8550

# Cria usuário e grupo não-root por segurança
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -s /bin/bash appuser

# Copia pacotes python instalados do builder para o usuário appuser
COPY --from=builder --chown=appuser:appgroup /root/.local /home/appuser/.local

# Copia o código-fonte da aplicação
COPY --chown=appuser:appgroup . /app

USER appuser

EXPOSE 8550

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8550').read()" || exit 1

CMD ["python", "app.py"]
