# Fix settings.py - hapus semua SPECTACULAR yang ada, bikin bersih
with open('core/settings.py', 'r') as f:
    lines = f.readlines()

result = []
skip = False
for i, line in enumerate(lines):
    if 'SPECTACULAR_SETTINGS' in line and '{' in line:
        skip = True
    if skip:
        if line.strip() == '}':
            skip = False
        continue
    if "# Sidecar static" in line:
        continue
    if "SPECTACULAR_SETTINGS['" in line:
        continue
    if "'drf_spectacular_sidecar'" in line:
        continue
    if "'drf_spectacular.plumbing'" in line:
        continue
    result.append(line)

# Tambah SPECTACULAR_SETTINGS bersih di akhir
result.append("""
SPECTACULAR_SETTINGS = {
    'TITLE': 'BlackMess API',
    'DESCRIPTION': 'BlackMess — Enterprise Secure Messaging Platform with E2EE, PQC & OJK Compliance',
    'VERSION': '2.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
    },
}
""")

with open('core/settings.py', 'w') as f:
    f.writelines(result)

print("settings.py Done!")
