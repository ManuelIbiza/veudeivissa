#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

python manage.py shell -c "
import os
from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

print('Comprobando variables de superusuario...')

if username and email and password:
    user = User.objects.filter(username=username).first()

    if user:
        print('Superusuario ya existe.')
    else:
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print('Superusuario creado correctamente.')
else:
    print('Variables de superusuario no configuradas.')
"

if [ -f datos_render.json ]; then
    echo "Importando datos_render.json..."
    python manage.py loaddata datos_render.json
    echo "Datos importados correctamente."
else
    echo "No se encontró datos_render.json."
fi

python manage.py shell -c "
from core.models import SiteConfiguration, HeroImage, AboutImage, EventFormat, MusicTrack, Reservation, ContactMessage
from musicians.models import Musician

print('--- CONTEO EN BASE DE DATOS RENDER ---')
print('SiteConfiguration:', SiteConfiguration.objects.count())
print('HeroImage:', HeroImage.objects.count())
print('AboutImage:', AboutImage.objects.count())
print('EventFormat:', EventFormat.objects.count())
print('MusicTrack:', MusicTrack.objects.count())
print('Reservation:', Reservation.objects.count())
print('ContactMessage:', ContactMessage.objects.count())
print('Musician:', Musician.objects.count())
print('--------------------------------------')
"