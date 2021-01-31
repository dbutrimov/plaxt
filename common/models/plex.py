from django.contrib.auth.models import User
from django.db import models


class PlexServer(models.Model):
    connection = models.CharField(max_length=128)
    sync_at = models.DateTimeField(null=True)


class PlexAccount(models.Model):
    uuid = models.CharField(max_length=64, db_index=True)
    username = models.CharField(max_length=64, db_index=True)
    token = models.CharField(max_length=32)

    server = models.ForeignKey(PlexServer, null=True, on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if self.server:
            self.server.save()

        super(PlexAccount, self).save(*args, **kwargs)
