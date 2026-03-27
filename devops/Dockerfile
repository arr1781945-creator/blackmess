FROM python:3.12-slim-bookworm AS base

LABEL maintainer="BlackMess Platform Team"
LABEL description="BlackMess — Enterprise Remote Work Platform"

# 1. Environment & Path (Tetap di atas)
ENV LD_LIBRARY_PATH=/usr/local/lib
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 2. Install dependensi sistem (Tetap sebagai root)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libffi-dev libssl-dev libpq-dev \
    git curl cmake ninja-build python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Build liboqs TANPA TEST & Tanpa -j 1 (Biar cepet karena filenya dikit)
RUN git clone --depth 1 https://github.com /tmp/liboqs && \
    cmake -S /tmp/liboqs -B /tmp/liboqs/build \
    -DOQS_DIST_BUILD=ON \
    -DBUILD_SHARED_LIBS=ON \
    -DOQS_BUILD_ONLY_LIB=ON \
    -DCMAKE_BUILD_TYPE=Release \
    -GNinja && \
    ninja -C /tmp/liboqs/build install && \
    ldconfig && \
    rm -rf /tmp/liboqs

# 4. Install python wrapper & upgrade pip (Gunakan flag biar gak error lagi)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --disable-pip-version-check liboqs-python

# 5. Baru buat User & Set Permission (DI SINI TEMPATNYA)
RUN groupadd -r blackmess && useradd -r -g blackmess -d /app -s /sbin/nologin blackmess && \
    chown -R blackmess:blackmess /app

# 6. Copy Source Code & Pindah ke User Non-Root
COPY . .
USER blackmess

# Jalankan aplikasi (Ganti sesuai nama project lo)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]

