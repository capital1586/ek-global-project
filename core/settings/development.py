
import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from urllib.parse import urlparse

try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo


load_dotenv(find_dotenv(".env.development", raise_error_if_not_found=False))

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = os.getenv("DEBUG", "false").lower() == "true"


APPLICATION_NAME = os.getenv("APPLICATION_NAME")

APPLICATION_ALIAS = os.getenv("APPLICATION_ALIAS")

INSTALLED_APPS = [
    # "django_q",  # Temporarily commented out to fix import error
    # Default apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.humanize",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Installed apps
    "apps.dashboard",
    "apps.accounts",
    "apps.portfolios",
    "apps.stocks",
    "apps.risk_management",  # Temporarily commented out due to numpy dependency
    "apps.live_rates",
    "apps.stockscreener",
    "apps.copilot",
    "apps.psxscreener",
    "apps.News",
    "apps.SmartScreener",
    "apps.Academy",
    "apps.Fullview",
    "apps.Alerts"
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

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "helpers.context_processors.application",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# DATABASES = {
#         "default": {
#             "ENGINE": "django.db.backends.sqlite3",
#             "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
#         }
#     }

# Replace the DATABASES section of your settings.py with this
tmpPostgres = urlparse(os.getenv("DATABASE_URL"))
# try:
#     import psycopg2
DATABASES = {
                        'default': {
                            'ENGINE': 'django.db.backends.postgresql',
                            'NAME': tmpPostgres.path.replace('/', ''),
                            'USER': tmpPostgres.username,
                            'PASSWORD': tmpPostgres.password,
                            'HOST': tmpPostgres.hostname,
                            'PORT': 5432,
                        }
                    }
# except ImportError:
#     # Fallback to SQLite if PostgreSQL is not available
#     DATABASES = {
#         "default": {
#             "ENGINE": "django.db.bckends.sqliate3",
#             "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
#         }
#     }

CONN_MAX_AGE = 15

# # Redis Configuration
# REDIS_HOST = os.getenv("REDIS_HOST")
# REDIS_PORT = os.getenv("REDIS_PORT")
# REDIS_USER = os.getenv("REDIS_USER")
# REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

# REDIS_LOCATION = f"rediss://{REDIS_USER}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"

# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": REDIS_LOCATION,
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#             "PASSWORD": REDIS_PASSWORD,
#         }
#     }
# }

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

AUTH_USER_MODEL = "accounts.UserAccount"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTHENTICATION_BACKENDS = [
    "apps.accounts.auth_backends.EmailBackend",
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles/")


STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "theme_files"),
    os.path.join(BASE_DIR, "core/static"),
    
    # Remove line, directory doesn't exist:
    # os.path.join(BASE_DIR, "static"),
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:signin"

if DEBUG is False:
    # PRODUCTION SETTINGS ONLY
    ALLOWED_HOSTS = ["doulab.project.bytechain.dev", "193.180.209.63"]

else:
    # DEVELOPMENT SETTINGS ONLY
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "doulab.project.bytechain.dev", "*"]


CSRF_TRUSTED_ORIGINS = ["https://doulab.project.bytechain.dev", 'https://0aed-182-191-170-203.ngrok-free.app']

####################
# HELPERS SETTINGS #
####################

# HELPERS_SETTINGS = {
#     "MAINTENANCE_MODE": {
#         "status": os.getenv("MAINTENANCE_MODE", "off").lower() in ["on", "true"],
#         "message": os.getenv("MAINTENANCE_MODE_MESSAGE", "default:minimal_dark"),
#     },
# }

MG_LINK_CLIENT_USERNAME = os.getenv("MG_LINK_CLIENT_USERNAME", "EKCapital2024")
MG_LINK_CLIENT_PASSWORD = os.getenv("MG_LINK_CLIENT_PASSWORD", "3KC@Pit@L!2024")

# Comment out Django-Q cluster settings

# Q_CLUSTER = {
#     "name": "ekg-global",
#     "recycle": 500,
#     "compress": True,
#     "save_limit": 250,
#     "queue_limit": 500,
#     "timeout": 300,
#     "retry": 330,
#     "max_attempts": 1,
#     "cpu_affinity": 1,
#     "workers": 2,
#     "label": "Django Q",
#     "catch_up": False,
#     "broker": f"redis://{REDIS_USER}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}",
# }


STOCKS_INDICES_FILE = os.path.join(BASE_DIR, "resources/stocks_indices.csv")

PAKISTAN_TIMEZONE = zoneinfo.ZoneInfo("Asia/Karachi")

# Logging Configuration
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {
#             'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
#             'style': '{',
#         },
#     },
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#             'formatter': 'verbose',
#         },
#     },
#     'root': {
#         'handlers': ['console'],
#         'level': 'INFO',
#     },
#     'loggers': {
#         'apps.SmartScreener': {
#             'handlers': ['console'],
#             'level': 'DEBUG',
#             'propagate': True,
#         },
#     },
# }
