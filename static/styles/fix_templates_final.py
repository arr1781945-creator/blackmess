with open(r'core/settings.py', 'r') as f:
    c = f.read()

old = """        r'APP_DIRS': False,
        r'loaders': [('django.template.loaders.filesystem.Loader', [str(BASE_DIR / 'templates')]), 'django.template.loaders.app_directories.Loader'],
        r'OPTIONS': {"""

new = """        r'APP_DIRS': False,
        r'OPTIONS': {
            r'loaders': [
                r'django.template.loaders.filesystem.Loader',
                r'django.template.loaders.app_directories.Loader',
            ],"""

c = c.replace(old, new)

with open(r'core/settings.py', 'w') as f:
    f.write(c)

print("Done!")
