from decouple import Csv, config

from .base import *  # noqa: F403

DEBUG = True

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1,testserver",
    cast=Csv(),
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in config("CSRF_TRUSTED_ORIGINS", default="http://127.0.0.1:8000,http://localhost:8000").split(",")
    if o.strip()
]
