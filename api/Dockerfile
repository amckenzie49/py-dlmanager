FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SHELVE_DB_PATH=/data/downloads

WORKDIR /app

COPY api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --system --uid 10001 --no-create-home app \
    && mkdir -p /data \
    && chown app:app /data

COPY api ./api

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"

CMD ["fastapi", "run", "api/main.py", "--host", "0.0.0.0", "--port", "8000"]