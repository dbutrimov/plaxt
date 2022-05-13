from .common import ENV

CELERY_TIMEZONE = ENV.str('TIME_ZONE', default='UTC')
CELERY_ENABLE_UTC = True

CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_IGNORE_RESULT = False
CELERY_TASK_TIME_LIMIT = 10 * 60  # 10 min
CELERY_RESULT_EXPIRES = 24 * 60 * 60  # 1 day

CELERY_BROKER_URL = ENV.str('CELERY_BROKER_URL', default='amqp://guest:guest@localhost:5672//')
CELERY_RESULT_BACKEND = ENV.str('CELERY_RESULT_BACKEND', default='django-db')

CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
