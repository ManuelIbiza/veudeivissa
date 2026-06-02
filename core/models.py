from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import get_language


def get_translated_field(obj, field_name):
    language = get_language()

    if language == 'ca':
        translated_value = getattr(obj, f'{field_name}_ca', '')

        if translated_value:
            return translated_value

    if language == 'en':
        translated_value = getattr(obj, f'{field_name}_en', '')

        if translated_value:
            return translated_value

    return getattr(obj, field_name)


class SiteConfiguration(models.Model):
    site_name = models.CharField(
        max_length=100,
        default="Veu d'Eivissa"
    )

    hero_title = models.CharField(
        max_length=150,
        blank=True
    )

    hero_title_ca = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Título hero en catalán'
    )

    hero_title_en = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Título hero en inglés'
    )

    hero_subtitle = models.TextField(
        blank=True
    )

    hero_subtitle_ca = models.TextField(
        blank=True,
        verbose_name='Subtítulo hero en catalán'
    )

    hero_subtitle_en = models.TextField(
        blank=True,
        verbose_name='Subtítulo hero en inglés'
    )

    about_title = models.CharField(
        max_length=150,
        blank=True,
        default='Servicios musicales a medida'
    )

    about_title_ca = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Título about en catalán'
    )

    about_title_en = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Título about en inglés'
    )

    about_text = models.TextField(
        blank=True
    )

    about_text_ca = models.TextField(
        blank=True,
        verbose_name='Texto about en catalán'
    )

    about_text_en = models.TextField(
        blank=True,
        verbose_name='Texto about en inglés'
    )

    contact_email = models.EmailField(
        blank=True
    )

    contact_phone = models.CharField(
        max_length=20,
        blank=True
    )

    whatsapp = models.CharField(
        max_length=20,
        blank=True
    )

    address = models.CharField(
        max_length=200,
        blank=True
    )

    instagram_url = models.URLField(
        blank=True
    )

    facebook_url = models.URLField(
        blank=True
    )

    tiktok_url = models.URLField(
        blank=True
    )

    spotify_url = models.URLField(
        blank=True
    )

    logo = models.ImageField(
        upload_to='core/',
        blank=True,
        null=True
    )

    hero_image = models.ImageField(
        upload_to='core/hero/',
        blank=True,
        null=True
    )

    about_image = models.ImageField(
        upload_to='core/about/',
        blank=True,
        null=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = 'Configuración del sitio'
        verbose_name_plural = 'Configuración del sitio'

    def __str__(self):
        return self.site_name

    @property
    def translated_hero_title(self):
        return get_translated_field(self, 'hero_title')

    @property
    def translated_hero_subtitle(self):
        return get_translated_field(self, 'hero_subtitle')

    @property
    def translated_about_title(self):
        return get_translated_field(self, 'about_title')

    @property
    def translated_about_text(self):
        return get_translated_field(self, 'about_text')

    def clean(self):
        if not self.pk and SiteConfiguration.objects.exists():
            raise ValidationError('Solo puede existir una configuración del sitio.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'site_name': "Veu d'Eivissa",
                'hero_title': 'Música en vivo para eventos privados en Ibiza',
                'hero_subtitle': 'Música en vivo para eventos privados y celebraciones especiales en Ibiza.',
                'about_title': 'Servicios musicales a medida',
                'about_text': 'Seleccionamos músicos profesionales para bodas, eventos privados, villas, beach clubs y celebraciones especiales en Ibiza.',
                'contact_email': 'info@veudeivissa.com',
            }
        )

        return obj


class HeroImage(models.Model):
    title = models.CharField(
        max_length=120,
        blank=True
    )

    image = models.ImageField(
        upload_to='core/hero/'
    )

    is_active = models.BooleanField(
        default=True
    )

    display_order = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['display_order', 'id']
        verbose_name = 'Imagen hero'
        verbose_name_plural = 'Imágenes hero'

    def __str__(self):
        if self.title:
            return self.title

        return f'Imagen hero {self.id}'


class AboutImage(models.Model):
    title = models.CharField(
        max_length=120,
        blank=True
    )

    image = models.ImageField(
        upload_to='core/about/'
    )

    is_active = models.BooleanField(
        default=True
    )

    display_order = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['display_order', 'id']
        verbose_name = 'Imagen about'
        verbose_name_plural = 'Imágenes about'

    def __str__(self):
        if self.title:
            return self.title

        return f'Imagen about {self.id}'


class MusicTrack(models.Model):
    title = models.CharField(
        max_length=120
    )

    title_ca = models.CharField(
        max_length=120,
        blank=True,
        verbose_name='Título en catalán'
    )

    title_en = models.CharField(
        max_length=120,
        blank=True,
        verbose_name='Título en inglés'
    )

    spotify_url = models.URLField(
        max_length=500,
        help_text='Puedes pegar una URL normal o una URL embed de Spotify.'
    )

    is_active = models.BooleanField(
        default=True
    )

    display_order = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['display_order', 'id']
        verbose_name = 'Canción de Spotify'
        verbose_name_plural = 'Canciones de Spotify'

    def __str__(self):
        return self.title

    @property
    def translated_title(self):
        return get_translated_field(self, 'title')

    def clean(self):
        super().clean()

        if not self.spotify_url:
            return

        normalized_url = self.get_normalized_spotify_url(self.spotify_url)

        if not normalized_url:
            raise ValidationError({
                'spotify_url': 'Introduce una URL válida de Spotify.'
            })

        self.spotify_url = normalized_url

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @staticmethod
    def get_normalized_spotify_url(url):
        parsed_url = urlparse(url)

        if parsed_url.netloc not in ['open.spotify.com', 'www.open.spotify.com']:
            return None

        path_parts = [
            part for part in parsed_url.path.split('/')
            if part
        ]

        if not path_parts:
            return None

        allowed_types = ['track', 'playlist', 'album']

        if path_parts[0] == 'embed':
            if len(path_parts) < 3:
                return None

            spotify_type = path_parts[1]
            spotify_id = path_parts[2]

        elif path_parts[0].startswith('intl-'):
            if len(path_parts) < 3:
                return None

            spotify_type = path_parts[1]
            spotify_id = path_parts[2]

        else:
            if len(path_parts) < 2:
                return None

            spotify_type = path_parts[0]
            spotify_id = path_parts[1]

        if spotify_type not in allowed_types:
            return None

        if not spotify_id:
            return None

        return f'https://open.spotify.com/embed/{spotify_type}/{spotify_id}'


class EventFormat(models.Model):
    title = models.CharField(
        max_length=120
    )

    title_ca = models.CharField(
        max_length=120,
        blank=True,
        verbose_name='Título en catalán'
    )

    title_en = models.CharField(
        max_length=120,
        blank=True,
        verbose_name='Título en inglés'
    )

    description = models.TextField()

    description_ca = models.TextField(
        blank=True,
        verbose_name='Descripción en catalán'
    )

    description_en = models.TextField(
        blank=True,
        verbose_name='Descripción en inglés'
    )

    image = models.ImageField(
        upload_to='core/formats/',
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    display_order = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['display_order', 'id']
        verbose_name = 'Formato'
        verbose_name_plural = 'Formatos'

    def __str__(self):
        return self.title

    @property
    def translated_title(self):
        return get_translated_field(self, 'title')

    @property
    def translated_description(self):
        return get_translated_field(self, 'description')


class ContactMessage(models.Model):
    name = models.CharField(
        max_length=100
    )

    email = models.EmailField()

    subject = models.CharField(
        max_length=150
    )

    message = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    answered = models.BooleanField(
        default=False
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Mensaje de contacto'
        verbose_name_plural = 'Mensajes de contacto'

    def __str__(self):
        return f"{self.name} - {self.subject}"


class Reservation(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente'),
        (STATUS_CONFIRMED, 'Confirmada'),
        (STATUS_CANCELLED, 'Cancelada'),
        (STATUS_COMPLETED, 'Completada'),
    ]

    client_name = models.CharField(
        max_length=120,
        verbose_name='Nombre del cliente'
    )

    client_email = models.EmailField(
        verbose_name='Email del cliente'
    )

    client_phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Teléfono del cliente'
    )

    event_date = models.DateField(
        verbose_name='Fecha del evento'
    )

    event_time = models.TimeField(
        blank=True,
        null=True,
        verbose_name='Hora aproximada'
    )

    event_location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Lugar del evento'
    )

    event_type = models.CharField(
        max_length=120,
        blank=True,
        verbose_name='Tipo de evento'
    )

    guests = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Número de invitados'
    )

    preferred_format = models.ForeignKey(
        EventFormat,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='reservations',
        verbose_name='Formato preferido'
    )

    preferred_musician = models.ForeignKey(
        'musicians.Musician',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='reservations',
        verbose_name='Músico preferido'
    )

    message = models.TextField(
        blank=True,
        verbose_name='Mensaje'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='Estado'
    )

    internal_notes = models.TextField(
        blank=True,
        verbose_name='Notas internas'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de solicitud'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'

    def __str__(self):
        return f'{self.client_name} - {self.event_date}'