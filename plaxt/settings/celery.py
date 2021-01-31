# # Celery Configuration Options
# CELERY_TIMEZONE = TIME_ZONE
# CELERY_TASK_TRACK_STARTED = True
# CELERY_TASK_TIME_LIMIT = 30 * 60
#
# CELERY_BROKER_URL = 'amqp://guest@localhost'
#
# #: Only add pickle to this list if your broker is secured
# #: from unwanted access (see userguide/security.html)
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_RESULT_BACKEND = 'django-db'  # 'db+sqlite:///results.sqlite'
# CELERY_TASK_SERIALIZER = 'json'
#
# CELERY_BEAT_SCHEDULE = {
#     'sync': {
#         'task': 'accounts.tasks.sync',
#         'schedule': 30.0,
#     },
# }
