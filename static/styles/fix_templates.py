with open(r'core/settings.py', 'r') as f:
    c = f.read()

c = c.replace(
    "r'APP_DIRS': True,",
    "r'APP_DIRS': False,\n        'loaders': [('django.template.loaders.filesystem.Loader', [str(BASE_DIR / 'templates')]), 'django.template.loaders.app_directories.Loader'],"
)

with open(r'core/settings.py', 'w') as f:
    f.write(c)

print("Done!")
