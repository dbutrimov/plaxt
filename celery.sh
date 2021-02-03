#!/bin/bash

celery --app plaxt worker --beat --loglevel INFO
