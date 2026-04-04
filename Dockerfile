FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Dépendances pour compiler mysqlclient / mariadbclient
RUN apt-get update && apt-get install -y \
    build-essential \
    libmariadb-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# =============================
# ==== IMAGE FINALE ===========
# =============================
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Dépendances RUNTIME MariaDB
RUN apt-get update && apt-get install -y \
    libmariadb3 \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier les packages Python buildés
COPY --from=builder /install /usr/local

# Copier ton code
COPY . .

EXPOSE 8000

CMD ["gunicorn", "service_authentification.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
#
