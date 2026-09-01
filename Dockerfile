# DAMGA-OPS backend (FastAPI deterministic Facts Engine + REST API).
# Frontend is deployed separately (Vercel); this image serves /api only.
FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .
RUN chmod +x docker-entrypoint.sh

# PaaS platforms inject $PORT; default matches local dev.
EXPOSE 8000
CMD ["./docker-entrypoint.sh"]
