with open(r'core/settings.py', 'r') as f:
    c = f.read()

c = c.replace(
    "    r'drf_spectacular',",
    "    r'drf_spectacular',\n    'drf_spectacular.plumbing',\n    'drf_spectacular_sidecar',"
)

with open(r'core/settings.py', 'w') as f:
    f.write(c)

print("Done!")
