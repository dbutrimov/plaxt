from django.db import models


class PlexAccount(models.Model):
    uuid = models.CharField(max_length=64, db_index=True)
    username = models.CharField(max_length=64, db_index=True)
    token = models.CharField(max_length=32)


class TraktAuth(models.Model):
    access_token = models.CharField(max_length=64)
    token_type = models.CharField(max_length=32)
    expires_in = models.IntegerField()
    refresh_token = models.CharField(max_length=64)
    scope = models.CharField(max_length=32, null=True)
    created_at = models.IntegerField()

    def from_response(self, response: dict):
        self.access_token = response['access_token']
        self.token_type = response['token_type']
        self.expires_in = response['expires_in']
        self.refresh_token = response['refresh_token']
        self.scope = response['scope']
        self.created_at = response['created_at']
        return self

    def to_response(self):
        return {
            'access_token': self.access_token,
            'token_type': self.token_type,
            'expires_in': self.expires_in,
            'refresh_token': self.refresh_token,
            'scope': self.scope,
            'created_at': self.created_at,
        }


class TraktAccount(models.Model):
    uuid = models.CharField(max_length=64, unique=True, db_index=True)
    username = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now=True)

    auth = models.ForeignKey(TraktAuth, on_delete=models.CASCADE)
    plex_account = models.ForeignKey(PlexAccount, null=True, on_delete=models.CASCADE)
