FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential git && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY solbot /app/solbot
COPY scripts /app/scripts

CMD ["python", "-m", "solbot"]
