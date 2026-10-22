"""Configuration du site des remarques A3H.

Tout ce qui change selon l'endroit (ton poste, Render, le serveur DGI) se règle par des
variables d'environnement : aucun secret n'est écrit dans ce fichier.
"""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# Render définit automatiquement la variable RENDER.
SUR_RENDER = bool(os.environ.get("RENDER"))
DEBUG = os.environ.get("DEBUG", "0" if SUR_RENDER else "1") == "1"

SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "cle-de-developpement-seulement"
    else:
        raise ImproperlyConfigured("Définissez la variable d'environnement SECRET_KEY.")

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
ALLOWED_HOSTS += [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]
_hote_render = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if _hote_render:
    ALLOWED_HOSTS.append(_hote_render)
    CSRF_TRUSTED_ORIGINS.append("https://" + _hote_render)

# HTTPS : actif sur Render ; à mettre HTTPS=0 sur un réseau interne en http.
HTTPS = os.environ.get("HTTPS", "1" if SUR_RENDER else "0") == "1"
if HTTPS:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "remarques",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "pageweb.urls"
WSGI_APPLICATION = "pageweb.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

# Base de données : SQLite par défaut ; PostgreSQL si DATABASE_URL est définie.
if os.environ.get("DATABASE_URL"):
    import dj_database_url
    DATABASES = {"default": dj_database_url.parse(os.environ["DATABASE_URL"], conn_max_age=600)}
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

LANGUAGE_CODE = "fr"
TIME_ZONE = "Africa/Tunis"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "remarques:accueil"
LOGOUT_REDIRECT_URL = "login"

# Captures d'écran : dossier privé, jamais servi directement (voir le LISEZMOI).
REMARQUES_CAPTURES_DIR = os.environ.get("REMARQUES_CAPTURES_DIR", str(BASE_DIR / "captures_privees"))
