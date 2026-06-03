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

if not username:
    print('Falta DJANGO_SUPERUSER_USERNAME')

if not email:
    print('Falta DJANGO_SUPERUSER_EMAIL')

if not password:
    print('Falta DJANGO_SUPERUSER_PASSWORD')

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