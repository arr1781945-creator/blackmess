with open(r'Dockerfile', 'r') as f:
    c = f.read()

# Ganti FROM biasa ke image yang udah ada liboqs
c = c.replace(
    r'FROM python:3.12-slim',
    r'FROM openquantumsafe/liboqs-python:latest'
)

# Hapus build liboqs manual karena udah ada di base image
old = """# Build liboqs dari source (setelah requirements supaya cache bust kalau requirements berubah)
RUN git clone --depth 1 https://github.com/open-quantum-safe/liboqs.git /tmp/liboqs \\
    && cmake -S /tmp/liboqs -B /tmp/liboqs/build \\
        -DOQS_DIST_BUILD=ON -DBUILD_SHARED_LIBS=ON -GNinja \\
    && cmake --build /tmp/liboqs/build -j4 \\
    && cmake --install /tmp/liboqs/build \\
    && ldconfig \\
    && pip install liboqs-python \\
    && rm -rf /tmp/liboqs"""

c = c.replace(old, "# liboqs already in base image")

with open(r'Dockerfile', 'w') as f:
    f.write(c)

print("Done!")
