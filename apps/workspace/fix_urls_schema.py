with open(r'core/urls.py', 'r') as f:
    c = f.read()

old = """schema_patterns = [
    path("api/schema/admin/",    SpectacularAPIView.as_view(urlconf="core.urls_admin"),    name="schema-admin"),
    path("api/schema/internal/", SpectacularAPIView.as_view(urlconf="core.urls_internal"), name="schema-internal"),
    path("api/schema/client/",   SpectacularAPIView.as_view(urlconf="core.urls_client"),   name="schema-client"),
    path("api/docs/admin/",    SpectacularSwaggerView.as_view(url_name="schema-admin"),    name="swagger-admin"),
    path("api/docs/internal/", SpectacularSwaggerView.as_view(url_name="schema-internal"), name="swagger-internal"),
    path("api/docs/client/",   SpectacularSwaggerView.as_view(url_name="schema-client"),   name="swagger-client"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema-admin"), name="redoc"),
]"""

new = """schema_patterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]"""

c = c.replace(old, new)

with open(r'core/urls.py', 'w') as f:
    f.write(c)

print("Done!")
