with open('core/settings.py', 'r') as f:
    c = f.read()

old = """        'APP_DIRS': False,
        'loaders': [('django.template.loaders.filesystem.Loader', [str(BASE_DIR / 'templates')]), 'django.template.loaders.app_directories.Loader'],
        'OPTIONS': {"""

new = """        'APP_DIRS': False,
        'OPTIONS': {
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],"""

c = c.replace(old, new)

with open('core/settings.py', 'w') as f:
    f.write(c)

print("Done!")
