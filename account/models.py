from django.db import models


class TraktAccount(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    username = models.CharField(max_length=255, unique=True)
    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255)
    updated_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now=True)
