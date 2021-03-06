"""
Django settings for brator project.

Generated by 'django-admin startproject' using Django 3.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

import os

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ["BRATOR_SECRET_KEY"]

DEBUG = os.environ.get("BRATOR_DEBUG", "").lower() in ("yes", "true")

ALLOWED_HOSTS = list(x for x in os.environ.get("BRATOR_ALLOWED_HOSTS", "").split(",") if x)

INSTALLED_APPS = [
    "whitenoise.runserver_nostatic",
    "compressor",
    "brator.quiz",
    "brator.users",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "rest_framework",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "beeline.middleware.django.HoneyMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ENVIRONMENT = os.environ.get("BRATOR_ENV_NAME", "unknown_env")

ROOT_URLCONF = 'brator.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'brator.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        "NAME": os.environ.get("BRATOR_DB_NAME", "brator_test"),
        "USER": os.environ.get("BRATOR_DB_USER", "brator_test"),
        "HOST": os.environ.get("BRATOR_DB_HOST", "localhost"),
        "PORT": os.environ.get("BRATOR_DB_PORT", "5432"),
        "PASSWORD": os.environ.get("BRATOR_DB_PASSWORD"),
        "ATOMIC_REQUESTS": True,
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "brator.renderer.PrettyJSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "EXCEPTION_HANDLER": "brator.exception_handlers.api_exception_handler",
    "PAGE_SIZE": 50,
    "COMPACT_JSON": False,
}

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
]

HONEYCOMB_API_KEY = os.environ.get("BRATOR_HONEYCOMB_API_KEY")
HONEYCOMB_DATASET = os.environ.get("BRATOR_HONEYCOMB_DATASET", ENVIRONMENT)
HONEYCOMB_SERVICE = os.environ.get("BRATOR_HONEYCOMB_SERVICE", "brator")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

LOGIN_REDIRECT_URL = "/"

COMPRESS_PRECOMPILERS = [
    ["text/x-scss", "django_libsass.SassCompiler"],
]
COMPRESS_ENABLED = True
