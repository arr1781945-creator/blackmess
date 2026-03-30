FROM python:3.12-slim
ARG CACHEBUST=1774837907

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    cmake \
    ninja-build \
    libssl-dev \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/open-quantum-safe/liboqs.git /tmp/liboqs && \
    cmake -S /tmp/liboqs -B /tmp/liboqs/build -DOQS_DIST_BUILD=ON -DBUILD_SHARED_LIBS=ON && \
    cmake --build /tmp/liboqs/build --parallel 4 && \
    cmake --install /tmp/liboqs/build && \
    pip install liboqs-python && \
    rm -rf /tmp/liboqs

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD sh -c 'python manage.py migrate --no-input && gunicorn core.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2'
# liboqs enabled Mon Mar 30 11:18:57 WIT 2026
