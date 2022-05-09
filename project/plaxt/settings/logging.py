import sys

from .common import ENV

logging_handlers = {
    'console': {
        'class': 'logging.StreamHandler',
        'stream': sys.stdout,
        'formatter': 'simple',
    },
}

log_filename = ENV.str('LOG_FILENAME', default=None)
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
        'level': ENV.str('LOG_LEVEL', default='INFO'),
    },
}
