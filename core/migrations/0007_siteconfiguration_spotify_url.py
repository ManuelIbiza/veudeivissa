# Generated manually to add Spotify URL to site configuration.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_musictrack'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteconfiguration',
            name='spotify_url',
            field=models.URLField(blank=True),
        ),
    ]