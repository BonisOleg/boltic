from pathlib import Path

from csp.constants import NONCE
from decouple import config
from django.templatetags.static import static

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY", default="django-insecure-boltiko-dev-change-me")

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "tinymce",
    "django_htmx",
    "csp",
    "apps.core",
    "apps.catalog",
    "apps.reviews",
    "apps.cart",
    "apps.orders",
    "apps.payments",
    "apps.accounts",
    "apps.content",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "csp.middleware.CSPMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "boltiko.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_settings",
                "apps.core.context_processors.cart_counter",
                "apps.core.context_processors.nav_catalog",
            ],
        },
    },
]

WSGI_APPLICATION = "boltiko.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "uk"
TIME_ZONE = "Europe/Kyiv"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Адмінка: ProductGroup з сотнями SKU-inline (автосаморізи ~219 × ~18 полів)
DATA_UPLOAD_MAX_NUMBER_FIELDS = config(
    "DATA_UPLOAD_MAX_NUMBER_FIELDS", default=20000, cast=int
)

# ERR-132: never default /admin/ — empty or literal "admin" → manage/
_admin_path = config("ADMIN_URL", default="manage").strip().strip("/")
if not _admin_path or _admin_path.lower() == "admin":
    _admin_path = "manage"
ADMIN_URL = f"{_admin_path}/"

# SEC-csp / project_structure §8.5 — Unfold needs CSP exempt (Alpine unsafe-eval)
# GTM (nonce на інлайн-сніпеті) + Ads/Analytics пікселі. Без прямого gtag.js.
_GTM_HOSTS = (
    "https://www.googletagmanager.com",
    "https://*.googletagmanager.com",
    "https://tagmanager.google.com",
)
_GA_ADS_HOSTS = (
    "https://www.google-analytics.com",
    "https://*.google-analytics.com",
    "https://analytics.google.com",
    "https://*.analytics.google.com",
    "https://www.googleadservices.com",
    "https://googleads.g.doubleclick.net",
    "https://*.g.doubleclick.net",
    "https://www.google.com",
    "https://www.google.com.ua",
    "https://*.google.com",
    "https://*.google.com.ua",
)
CONTENT_SECURITY_POLICY = {
    "EXCLUDE_URL_PREFIXES": (f"/{_admin_path}/", "/tinymce/"),
    "DIRECTIVES": {
        "default-src": ["'self'"],
        "script-src": ["'self'", NONCE, *_GTM_HOSTS, *_GA_ADS_HOSTS],
        # style= legacy + theme :root block; cleanup ≠ SEC-csp scope. ERR-106: no HTMX inject.
        "style-src": ["'self'", "'unsafe-inline'", "https://www.googletagmanager.com", "https://tagmanager.google.com"],
        "font-src": ["'self'", "data:"],
        "img-src": ["'self'", "data:", "blob:", *_GTM_HOSTS, *_GA_ADS_HOSTS],
        "connect-src": ["'self'", *_GTM_HOSTS, *_GA_ADS_HOSTS],
        "frame-src": [
            "https://www.googletagmanager.com",
            "https://td.doubleclick.net",
            "https://www.google.com",
        ],
        "frame-ancestors": ["'none'"],
        "base-uri": ["'self'"],
        "form-action": ["'self'", "https://www.liqpay.ua", "https://www.liqpay.com"],
        "object-src": ["'none'"],
    },
}

GTM_CONTAINER_ID = config("GTM_CONTAINER_ID", default="GTM-M63C7Z3F").strip()
GOOGLE_FEED_CACHE_SECONDS = config("GOOGLE_FEED_CACHE_SECONDS", default=1800, cast=int)

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/kabinet/"
LOGOUT_REDIRECT_URL = "/"

NOVA_POSHTA_API_KEY = config("NOVA_POSHTA_API_KEY", default="")

LIQPAY_PUBLIC_KEY = config("LIQPAY_PUBLIC_KEY", default="")
LIQPAY_PRIVATE_KEY = config("LIQPAY_PRIVATE_KEY", default="")
LIQPAY_SANDBOX = config("LIQPAY_SANDBOX", default=True, cast=bool)

EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@boltiko.local")

SITE_URL = config("SITE_URL", default="http://127.0.0.1:8000")

TINYMCE_DEFAULT_CONFIG = {
    "height": 400,
    "menubar": False,
    "plugins": "link lists image code",
    "toolbar": "undo redo | bold italic underline | bullist numlist | link image | code",
    "content_css": False,
    "skin": "oxide",
}


def _unfold_navigation(request):
    from apps.core.site_content_registry import build_unfold_navigation

    return build_unfold_navigation()


UNFOLD = {
    "SITE_TITLE": "БОЛТіК° Admin",
    "SITE_HEADER": "БОЛТіК° — Адмінпанель",
    "SITE_SYMBOL": "hardware",
    "SITE_URL": "/",
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "any",
            "href": lambda request: static("img/favicon.ico") + "?v=20260723h",
        },
        {
            "rel": "icon",
            "type": "image/png",
            "sizes": "32x32",
            "href": lambda request: static("img/favicon-32.png") + "?v=20260723h",
        },
        {
            "rel": "icon",
            "type": "image/png",
            "sizes": "48x48",
            "href": lambda request: static("img/favicon-48.png") + "?v=20260723h",
        },
        {
            "rel": "apple-touch-icon",
            "sizes": "180x180",
            "href": lambda request: static("img/apple-touch-icon.png") + "?v=20260723h",
        },
    ],
    "SIDEBAR": {
        "show_search": True,
        "command_search": True,
        "show_all_applications": False,
        "navigation": _unfold_navigation,
    },
}
