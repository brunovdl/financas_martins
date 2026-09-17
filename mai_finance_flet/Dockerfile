# ============================================================
# MAI Finance Flet Web App — Dockerfile (Subpasta mai_finance_flet)
# Build Context: mai_finance_flet/
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# 1. Dependências de sistema e libcap para vincular portas baixas (< 1024 como a porta 80)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libcap2-bin \
    && rm -rf /var/lib/apt/lists/* \
    && setcap 'cap_net_bind_service=+ep' /usr/local/bin/python3.11

# 2. Instala dependências Python no ambiente global do container
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copia o código-fonte da aplicação
COPY . /app

# 4. Cria usuário e grupo não-root por segurança
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -s /bin/bash appuser && \
    chown -R appuser:appgroup /app /home/appuser

USER appuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLET_HOST=0.0.0.0 \
    FLET_PORT=80 \
    PORT=80

EXPOSE 80 8550

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request, os; p = os.getenv('PORT', os.getenv('FLET_PORT', '80')); urllib.request.urlopen(f'http://127.0.0.1:{p}').read()" || exit 1

CMD ["python", "app.py"]
