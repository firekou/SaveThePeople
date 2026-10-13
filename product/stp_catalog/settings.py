"""SaveThePeople D1-A synthetic resource catalog — local-only settings.

DEBUG is always False so no traceback, setting or connection string can be
rendered to a browser. Values come from environment variables (see
.env.example); defaults are local synthetic test values only.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("STP_SECRET_KEY", "stp-d1a-local-synthetic-only-not-a-secret")
DEBUG = False
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

INSTALLED_APPS = [
    "catalog.apps.CatalogConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "stp_catalog.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["django.template.context_processors.request"]},
    }
]

WSGI_APPLICATION = "stp_catalog.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("STP_DB_NAME", "stp_catalog"),
        "USER": os.environ.get("STP_DB_USER", "stp_d1a"),
        "PASSWORD": os.environ.get("STP_DB_PASSWORD", ""),
        "HOST": os.environ.get("STP_DB_HOST", "/var/tmp/stp_d1a_pg/sock"),
        "PORT": os.environ.get("STP_DB_PORT", "54329"),
        "CONN_MAX_AGE": 0,
        "TEST": {"NAME": os.environ.get("STP_DB_NAME", "stp_catalog") + "_test"},
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "zh-hant"
TIME_ZONE = "Asia/Taipei"
USE_I18N = False
USE_TZ = True

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Path of the synthetic dataset used by `import_synthetic_catalog` (repo file; read-only).
STP_SYNTHETIC_DATASET = os.environ.get(
    "STP_SYNTHETIC_DATASET",
    str(BASE_DIR.parent / "docs" / "platform" / "examples" / "synthetic_resources.json"),
)
