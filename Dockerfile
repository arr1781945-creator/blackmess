FROM python:3.12-slim

WORKDIR /app

# System deps + liboqs build tools
RUN apt-get update && apt-get install -y \
    gcc g++ libpq-dev cmake ninja-build \
    libssl-dev python3-dev git build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps dulu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Build liboqs dari source (setelah requirements supaya cache bust kalau requirements berubah)
RUN git clone --depth 1 https://github.com/open-quantum-safe/liboqs.git /tmp/liboqs \
    && cmake -S /tmp/liboqs -B /tmp/liboqs/build \
        -DOQS_DIST_BUILD=ON -DBUILD_SHARED_LIBS=ON -GNinja \
    && cmake --build /tmp/liboqs/build -j4 \
    && cmake --install /tmp/liboqs/build \
    && ldconfig \
    && pip install liboqs-python \
    && rm -rf /tmp/liboqs

ARG CACHE_BUST=1
COPY . .

RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD sh -c 'python manage.py migrate --no-input && daphne -b 0.0.0.0 -p ${{PORT:-8000}} core.asgi:application'
# force Thu Apr  2 12:14:34 WIT 2026
