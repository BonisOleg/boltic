from .production import *  # noqa: F403

# TLS terminates in nginx. Gunicorn stays HTTP so /healthz/ is not 301.
SECURE_SSL_REDIRECT = False

_extra_hosts = ("web", "localhost", "127.0.0.1")
ALLOWED_HOSTS = list(dict.fromkeys([*ALLOWED_HOSTS, *_extra_hosts]))  # noqa: F405
