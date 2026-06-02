from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class BackofficeUserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='backoffice_profile'
    )

    can_manage_musicians = models.BooleanField(
        default=False,
        verbose_name='Puede añadir y eliminar músicos'
    )

    can_manage_site_sections = models.BooleanField(
        default=False,
        verbose_name='Puede editar secciones de la web'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = 'Perfil de usuario de backoffice'
        verbose_name_plural = 'Perfiles de usuarios de backoffice'

    def __str__(self):
        return f'Permisos de {self.user.username}'


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_backoffice_profile(sender, instance, created, **kwargs):
    if created:
        BackofficeUserProfile.objects.get_or_create(user=instance)