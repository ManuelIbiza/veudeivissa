from django import forms
from django.contrib.auth.models import User

from core.models import (
    AboutImage,
    EventFormat,
    HeroImage,
    MusicTrack,
    Reservation,
    SiteConfiguration,
)
from musicians.models import Musician

from .models import BackofficeUserProfile


class UniqueDisplayOrderMixin:
    def clean_display_order(self):
        display_order = self.cleaned_data.get('display_order')

        if display_order is None:
            return display_order

        duplicate_exists = self.Meta.model.objects.filter(
            display_order=display_order
        ).exclude(
            pk=self.instance.pk
        ).exists()

        if duplicate_exists:
            raise forms.ValidationError(
                'Ya existe una entrada con este número de orden. Elige otro número o usa las flechas de la lista para reordenar.'
            )

        return display_order


class MusicianForm(UniqueDisplayOrderMixin, forms.ModelForm):
    class Meta:
        model = Musician
        fields = [
            'name',
            'instrument',
            'instrument_ca',
            'instrument_en',
            'description',
            'description_ca',
            'description_en',
            'image',
            'is_active',
            'display_order',
        ]

        labels = {
            'name': 'Nombre artístico',
            'instrument': 'Instrumento en español',
            'instrument_ca': 'Instrumento en catalán',
            'instrument_en': 'Instrumento en inglés',
            'description': 'Descripción en español',
            'description_ca': 'Descripción en catalán',
            'description_en': 'Descripción en inglés',
            'image': 'Imagen',
            'is_active': 'Activo',
            'display_order': 'Orden',
        }

        widgets = {
            'image': forms.FileInput(
                attrs={
                    'class': 'styled-file-input',
                }
            ),
        }


class MusicianBasicForm(forms.ModelForm):
    class Meta:
        model = Musician
        fields = [
            'is_active',
        ]

        labels = {
            'is_active': 'Activo',
        }


class SiteConfigurationForm(forms.ModelForm):
    class Meta:
        model = SiteConfiguration
        fields = [
            'site_name',
            'contact_email',
            'contact_phone',
            'whatsapp',
            'address',
            'instagram_url',
            'facebook_url',
            'tiktok_url',
            'spotify_url',
            'logo',
        ]

        labels = {
            'site_name': 'Nombre del sitio',
            'contact_email': 'Correo de contacto',
            'contact_phone': 'Teléfono de contacto',
            'whatsapp': 'WhatsApp',
            'address': 'Dirección',
            'instagram_url': 'Instagram',
            'facebook_url': 'Facebook',
            'tiktok_url': 'TikTok',
            'spotify_url': 'Spotify',
            'logo': 'Logotipo',
        }

        widgets = {
            'logo': forms.FileInput(
                attrs={
                    'class': 'styled-file-input',
                }
            ),
        }


class HeroContentForm(forms.ModelForm):
    class Meta:
        model = SiteConfiguration
        fields = [
            'hero_title',
            'hero_title_ca',
            'hero_title_en',
            'hero_subtitle',
            'hero_subtitle_ca',
            'hero_subtitle_en',
        ]

        labels = {
            'hero_title': 'Título principal del hero en español',
            'hero_title_ca': 'Título principal del hero en catalán',
            'hero_title_en': 'Título principal del hero en inglés',
            'hero_subtitle': 'Contenido / subtítulo del hero en español',
            'hero_subtitle_ca': 'Contenido / subtítulo del hero en catalán',
            'hero_subtitle_en': 'Contenido / subtítulo del hero en inglés',
        }


class AboutContentForm(forms.ModelForm):
    class Meta:
        model = SiteConfiguration
        fields = [
            'about_title',
            'about_title_ca',
            'about_title_en',
            'about_text',
            'about_text_ca',
            'about_text_en',
        ]

        labels = {
            'about_title': 'Título de la sección About en español',
            'about_title_ca': 'Título de la sección About en catalán',
            'about_title_en': 'Título de la sección About en inglés',
            'about_text': 'Contenido de la sección About en español',
            'about_text_ca': 'Contenido de la sección About en catalán',
            'about_text_en': 'Contenido de la sección About en inglés',
        }


class HeroImageForm(UniqueDisplayOrderMixin, forms.ModelForm):
    class Meta:
        model = HeroImage
        fields = [
            'title',
            'image',
            'is_active',
            'display_order',
        ]

        labels = {
            'title': 'Título interno',
            'image': 'Imagen',
            'is_active': 'Activa',
            'display_order': 'Orden',
        }

        widgets = {
            'image': forms.FileInput(
                attrs={
                    'class': 'styled-file-input',
                }
            ),
        }


class AboutImageForm(UniqueDisplayOrderMixin, forms.ModelForm):
    class Meta:
        model = AboutImage
        fields = [
            'title',
            'image',
            'is_active',
            'display_order',
        ]

        labels = {
            'title': 'Título interno',
            'image': 'Imagen',
            'is_active': 'Activa',
            'display_order': 'Orden',
        }

        widgets = {
            'image': forms.FileInput(
                attrs={
                    'class': 'styled-file-input',
                }
            ),
        }


class MusicTrackForm(UniqueDisplayOrderMixin, forms.ModelForm):
    class Meta:
        model = MusicTrack
        fields = [
            'title',
            'spotify_url',
            'is_active',
            'display_order',
        ]

        labels = {
            'title': 'Título',
            'spotify_url': 'URL de Spotify',
            'is_active': 'Activa',
            'display_order': 'Orden',
        }

        help_texts = {
            'spotify_url': (
                'Puedes pegar una URL normal de Spotify o una URL embed. '
                'Por ejemplo: https://open.spotify.com/track/...'
            ),
            'display_order': 'Las canciones con menor número aparecerán antes.',
        }


class EventFormatForm(UniqueDisplayOrderMixin, forms.ModelForm):
    class Meta:
        model = EventFormat
        fields = [
            'title',
            'title_ca',
            'title_en',
            'description',
            'description_ca',
            'description_en',
            'image',
            'is_active',
            'display_order',
        ]

        labels = {
            'title': 'Título en español',
            'title_ca': 'Título en catalán',
            'title_en': 'Título en inglés',
            'description': 'Descripción en español',
            'description_ca': 'Descripción en catalán',
            'description_en': 'Descripción en inglés',
            'image': 'Imagen',
            'is_active': 'Activo',
            'display_order': 'Orden',
        }

        widgets = {
            'image': forms.FileInput(
                attrs={
                    'class': 'styled-file-input',
                }
            ),
        }


class ReservationBackofficeForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = [
            'status',
            'internal_notes',
        ]

        labels = {
            'status': 'Estado',
            'internal_notes': 'Notas internas',
        }

        widgets = {
            'internal_notes': forms.Textarea(
                attrs={
                    'rows': 6,
                    'placeholder': 'Añade aquí información interna sobre la reserva...',
                }
            ),
        }


class BackofficeUserCreateForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput
    )

    password2 = forms.CharField(
        label='Repetir contraseña',
        widget=forms.PasswordInput
    )

    can_manage_musicians = forms.BooleanField(
        label='Puede añadir y eliminar músicos',
        required=False
    )

    can_manage_site_sections = forms.BooleanField(
        label='Puede editar secciones de la web',
        required=False
    )

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'is_active',
        ]

        labels = {
            'username': 'Usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellidos',
            'email': 'Correo electrónico',
            'is_active': 'Activo',
        }

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Las contraseñas no coinciden.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True
        user.is_superuser = False
        user.set_password(self.cleaned_data['password1'])

        if commit:
            user.save()

            profile, _ = BackofficeUserProfile.objects.get_or_create(user=user)
            profile.can_manage_musicians = self.cleaned_data.get('can_manage_musicians', False)
            profile.can_manage_site_sections = self.cleaned_data.get('can_manage_site_sections', False)
            profile.save()

        return user


class BackofficeUserUpdateForm(forms.ModelForm):
    can_manage_musicians = forms.BooleanField(
        label='Puede añadir y eliminar músicos',
        required=False
    )

    can_manage_site_sections = forms.BooleanField(
        label='Puede editar secciones de la web',
        required=False
    )

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'is_active',
        ]

        labels = {
            'username': 'Usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellidos',
            'email': 'Correo electrónico',
            'is_active': 'Activo',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            profile, _ = BackofficeUserProfile.objects.get_or_create(user=self.instance)
            self.fields['can_manage_musicians'].initial = profile.can_manage_musicians
            self.fields['can_manage_site_sections'].initial = profile.can_manage_site_sections

            if self.instance.is_superuser:
                self.fields['can_manage_musicians'].disabled = True
                self.fields['can_manage_site_sections'].disabled = True
                self.fields['is_active'].disabled = True

    def save(self, commit=True):
        user = super().save(commit=False)

        if user.is_superuser:
            user.is_active = True

        if commit:
            user.save()

            profile, _ = BackofficeUserProfile.objects.get_or_create(user=user)

            if user.is_superuser:
                profile.can_manage_musicians = True
                profile.can_manage_site_sections = True
            else:
                profile.can_manage_musicians = self.cleaned_data.get('can_manage_musicians', False)
                profile.can_manage_site_sections = self.cleaned_data.get('can_manage_site_sections', False)

            profile.save()

        return user


ManagerCreateForm = BackofficeUserCreateForm
ManagerUpdateForm = BackofficeUserUpdateForm