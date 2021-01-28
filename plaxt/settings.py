import os
import sys

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Read environment variables
env = environ.Env()

env_file = env.str('ENV_FILE', default=os.path.join(BASE_DIR, '.env'))
environ.Env.read_env(env_file=env_file)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=False)

# Init logging
logging_handlers = {
    'console': {
        'class': 'logging.StreamHandler',
        'stream': sys.stdout,
        'formatter': 'simple',
    },
}

log_filename = env.str('LOG_FILENAME', default=None)
if log_filename:
    logging_handlers['file'] = {
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': log_filename,
        'maxBytes': 1048576,  # 1MB
        'backupCount': 5,
        'formatter': 'default',
    }

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': "%(levelname)-8s %(name)-24s %(message)s",
        },
        'default': {
            'format': "%(asctime)-24s %(levelname)-8s %(name)-24s %(message)s",
        },
    },
    'handlers': logging_handlers,
    'root': {
        'handlers': logging_handlers.keys(),
        'level': env.str('LOG_LEVEL', default='INFO'),
    },
}

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# Application definition

INSTALLED_APPS = ['whitenoise.runserver_nostatic'] if DEBUG else []
INSTALLED_APPS += [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_celery_results',
    'api',
    'account',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'plaxt.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
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

WSGI_APPLICATION = 'plaxt.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': env.db('DATABASE_URL'),
}


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = env.str('LANGUAGE_CODE', default='en-us')
TIME_ZONE = env.str('TIME_ZONE', default='UTC')
USE_I18N = env.bool('USE_I18N', default=True)
USE_L10N = env.bool('USE_L10N', default=True)
USE_TZ = env.bool('USE_TZ', default=True)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, "static"),
# ]


# Celery Configuration Options
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60

CELERY_BROKER_URL = 'amqp://guest@localhost'

#: Only add pickle to this list if your broker is secured
#: from unwanted access (see userguide/security.html)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_BACKEND = 'django-db'  # 'db+sqlite:///results.sqlite'
CELERY_TASK_SERIALIZER = 'json'

CELERY_BEAT_SCHEDULE = {
    'sync': {
        'task': 'account.tasks.sync',
        'schedule': 30.0,
    },
}
