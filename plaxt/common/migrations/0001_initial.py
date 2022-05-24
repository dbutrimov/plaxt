# Generated by Django 3.2.6 on 2021-08-16 22:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PlexServer',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('connection', models.CharField(max_length=128)),
                ('last_task_id', models.CharField(db_index=True, max_length=128, null=True)),
                ('last_sync_at', models.DateTimeField(db_index=True, null=True)),
                ('trakt_timestamp', models.DateTimeField(null=True)),
                ('plex_timestamp', models.DateTimeField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TraktAuth',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('access_token', models.CharField(max_length=64)),
                ('token_type', models.CharField(max_length=32)),
                ('expires_in', models.IntegerField()),
                ('refresh_token', models.CharField(max_length=64)),
                ('scope', models.CharField(max_length=32, null=True)),
                ('created_at', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='TraktAccount',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('uuid', models.CharField(db_index=True, max_length=64, unique=True)),
                ('username', models.CharField(db_index=True, max_length=64)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('auth', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='common.traktauth')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PlexAccount',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('uuid', models.CharField(db_index=True, max_length=64)),
                ('username', models.CharField(db_index=True, max_length=64)),
                ('token', models.CharField(max_length=32)),
                ('server', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='common.plexserver')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
