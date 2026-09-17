# ============================================================
# MAI Finance Flet Web App — Dockerfile Multi-Stage (Easypanel / Produção)
# Build Context: Raiz do repositório
# ============================================================

# Stage 1: Builder — instala dependências em ambiente isolado
FROM python:3.11-slim AS builder

WORKDIR /app

# Instala dependências de compilação se necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY mai_finance_flet/requirements.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============================================================
# Stage 2: Runner — imagem final de produção enxuta
# ============================================================
FROM python:3.11-slim AS runner

WORKDIR /app

# Instala libcap2-bin para permitir que o usuário não-root vincule portas baixas (< 1024 como a porta 80)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcap2-bin \
    && rm -rf /var/lib/apt/lists/* \
    && setcap 'cap_net_bind_service=+ep' /usr/local/bin/python3.11

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLET_HOST=0.0.0.0 \
    FLET_PORT=80 \
    PORT=80

# Cria usuário e grupo não-root por segurança
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -s /bin/bash appuser

# Copia pacotes python instalados do builder
COPY --from=builder /install /usr/local

# Copia o código-fonte da aplicação Flet para /app
COPY --chown=appuser:appgroup mai_finance_flet/ /app/

USER appuser

# Expõe a porta 80 (padrão do Easypanel) e 8550 (alternativa)
EXPOSE 80 8550

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request, os; p = os.getenv('PORT', os.getenv('FLET_PORT', '80')); urllib.request.urlopen(f'http://127.0.0.1:{p}').read()" || exit 1

CMD ["python", "app.py"]
