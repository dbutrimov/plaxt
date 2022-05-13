import os

from .common import BASE_DIR, ENV

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ENV.str('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = ENV.bool('DEBUG', default=False)

ALLOWED_HOSTS = ENV.list('ALLOWED_HOSTS', default=[])

# Application definition

INSTALLED_APPS = ['whitenoise.runserver_nostatic'] if DEBUG else []
INSTALLED_APPS += [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_celery_beat',
    'django_celery_results',
    'common',
    'accounts',
    'api',
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
    'default': ENV.db('DATABASE_URL'),
}

LOGIN_URL = '/login/'

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = ENV.str('LANGUAGE_CODE', default='en-us')
TIME_ZONE = ENV.str('TIME_ZONE', default='UTC')
USE_I18N = ENV.bool('USE_I18N', default=True)
USE_L10N = ENV.bool('USE_L10N', default=True)
USE_TZ = ENV.bool('USE_TZ', default=True)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, "static"),
# ]


AUTHENTICATION_BACKENDS = ['accounts.backends.TraktBackend']
