# Bersihkan settings.py dari duplikat SPECTACULAR_SETTINGS
with open('core/settings.py', 'r') as f:
    lines = f.readlines()

# Hapus semua baris SPECTACULAR yang duplikat di bawah
result = []
skip = False
spectacular_count = 0
for line in lines:
    if "SPECTACULAR_SETTINGS = {" in line:
        spectacular_count += 1
        if spectacular_count > 1:
            skip = True
    if skip and line.strip() == "}":
        skip = False
        continue
    if "SPECTACULAR_SETTINGS['" in line:
        continue
    if not skip:
        result.append(line)

with open('core/settings.py', 'w') as f:
    f.writelines(result)

# Bersihkan urls.py
with open('core/urls.py', 'r') as f:
    c = f.read()

c = c.replace(
    'from drf_spectacular.views import SpectacularAPIView\nfrom drf_spectacular_sidecar.renderers import OpenApiRendererMixin\nfrom drf_spectacular.views import SpectacularSwaggerView, SpectacularRedocView',
    'from drf_spectacular.views import (\n    SpectacularAPIView,\n    SpectacularSwaggerView,\n    SpectacularRedocView,\n)'
)

with open('core/urls.py', 'w') as f:
    f.write(c)

print("Done!")
