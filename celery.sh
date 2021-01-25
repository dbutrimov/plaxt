#!/bin/bash

celery --app plaxt worker --beat --loglevel INFO --logfile "logs/celery.log"
