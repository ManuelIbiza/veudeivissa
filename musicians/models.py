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


'''Clase Musician. Crea el objeto que el ORM gestionará para crear la tabla de músicos mostrados en la web.'''
class Musician(models.Model):
    name = models.CharField(
        max_length=120,
        verbose_name='Nombre artístico'
    )

    instrument = models.CharField(
        max_length=120,
        verbose_name='Instrumento'
    )

    instrument_ca = models.CharField(
        max_length=120,
        blank=True,
        verbose_name='Instrumento en catalán'
    )

    instrument_en = models.CharField(
        max_length=120,
        blank=True,
        verbose_name='Instrumento en inglés'
    )

    description = models.TextField(
        blank=True,
        verbose_name='Descripción breve'
    )

    description_ca = models.TextField(
        blank=True,
        verbose_name='Descripción breve en catalán'
    )

    description_en = models.TextField(
        blank=True,
        verbose_name='Descripción breve en inglés'
    )

    image = models.ImageField(
        upload_to='musicians/',
        blank=True,
        null=True,
        verbose_name='Imagen'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )

    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['display_order', 'id']
        verbose_name = 'Músico'
        verbose_name_plural = 'Músicos'

    def __str__(self):
        return f'{self.name} - {self.instrument}'

    @property
    def translated_instrument(self):
        return get_translated_field(self, 'instrument')

    @property
    def translated_description(self):
        return get_translated_field(self, 'description')