FROM openquantumsafe/liboqs-python:latest

WORKDIR /app

# System deps + liboqs build tools
RUN apt-get update && apt-get install -y \
    gcc g++ libpq-dev cmake ninja-build \
    libssl-dev python3-dev git build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps dulu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# liboqs already in base image

ARG CACHE_BUST=1
COPY . .

RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD sh -c 'python manage.py migrate --no-input && daphne -b 0.0.0.0 -p ${{PORT:-8000}} core.asgi:application'
# force Thu Apr  2 12:14:34 WIT 2026
