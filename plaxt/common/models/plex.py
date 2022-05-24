from django.contrib.auth.models import User
from django.db import models


class PlexServer(models.Model):
    id = models.AutoField(primary_key=True)
    connection = models.CharField(max_length=128)
    last_task_id = models.CharField(max_length=128, null=True, db_index=True)
    last_sync_at = models.DateTimeField(null=True, db_index=True)
    trakt_timestamp = models.DateTimeField(null=True)
    plex_timestamp = models.DateTimeField(null=True)


class PlexAccount(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.CharField(max_length=64, db_index=True)
    username = models.CharField(max_length=64, db_index=True)
    token = models.CharField(max_length=32)

    server = models.ForeignKey(PlexServer, null=True, on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if self.server:
            self.server.save()

        super(PlexAccount, self).save(*args, **kwargs)
