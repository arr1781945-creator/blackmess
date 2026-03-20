FROM python:3.12-slim-bookworm AS base

LABEL maintainer="BlackMess Platform Team"
LABEL description="BlackMess — Enterprise Remote Work Platform"

# Security: non-root user
RUN groupadd -r blackmess && useradd -r -g blackmess -d /app -s /sbin/nologin blackmess

WORKDIR /app

# System dependencies + liboqs build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libffi-dev libssl-dev libpq-dev \
    git curl cmake ninja-build python3-dev \
    astyle doxygen valgrind \
    && rm -rf /var/lib/apt/lists/*

# Build liboqs dari source
RUN git clone --depth 1 https://github.com/open-quantum-safe/liboqs.git /tmp/liboqs && \
    cmake -S /tmp/liboqs -B /tmp/liboqs/build \
    -DOQS_DIST_BUILD=ON \
    -DBUILD_SHARED_LIBS=ON \
    -DCMAKE_BUILD_TYPE=Release \
    -GNinja && \
    ninja -C /tmp/liboqs/build && \
    ninja -C /tmp/liboqs/build install && \
    ldconfig && \
    rm -rf /tmp/liboqs

# Build liboqs-python
RUN pip install --no-cache-dir liboqs-python

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput || true

RUN chown -R blackmess:blackmess /app

USER blackmess

ENV DJANGO_SETTINGS_MODULE=myproject.settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

CMD ["gunicorn", "myproject.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]
