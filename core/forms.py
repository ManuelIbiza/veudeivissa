from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from musicians.models import Musician

from .models import EventFormat, Reservation


class TranslatedEventFormatChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.translated_title


class TranslatedMusicianChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{obj.name} - {obj.translated_instrument}'


class ReservationForm(forms.ModelForm):
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'reservation-form__honeypot',
                'autocomplete': 'off',
                'tabindex': '-1',
            }
        )
    )

    preferred_format = TranslatedEventFormatChoiceField(
        queryset=EventFormat.objects.none(),
        required=True,
        empty_label=_('Selecciona un formato'),
        widget=forms.Select(
            attrs={
                'class': 'reservation-form__input reservation-form__select',
                'required': 'required',
            }
        )
    )

    preferred_musician = TranslatedMusicianChoiceField(
        queryset=Musician.objects.none(),
        required=True,
        empty_label=_('Selecciona un músico'),
        widget=forms.Select(
            attrs={
                'class': 'reservation-form__input reservation-form__select',
                'required': 'required',
            }
        )
    )

    class Meta:
        model = Reservation

        fields = [
            'client_name',
            'client_email',
            'client_phone',
            'event_date',
            'event_time',
            'event_location',
            'event_type',
            'guests',
            'preferred_format',
            'preferred_musician',
            'message',
        ]

        labels = {
            'client_name': _('Nombre'),
            'client_email': _('Email'),
            'client_phone': _('Teléfono'),
            'event_date': _('Fecha del evento'),
            'event_time': _('Hora aproximada'),
            'event_location': _('Lugar del evento'),
            'event_type': _('Tipo de evento'),
            'guests': _('Número de invitados'),
            'preferred_format': _('Formato preferido'),
            'preferred_musician': _('Músico preferido'),
            'message': _('Mensaje'),
        }

        widgets = {
            'client_name': forms.TextInput(
                attrs={
                    'class': 'reservation-form__input',
                    'placeholder': _('Tu nombre'),
                    'required': 'required',
                }
            ),
            'client_email': forms.EmailInput(
                attrs={
                    'class': 'reservation-form__input',
                    'placeholder': _('tu@email.com'),
                    'required': 'required',
                }
            ),
            'client_phone': forms.TextInput(
                attrs={
                    'class': 'reservation-form__input',
                    'placeholder': _('+34 600 000 000'),
                    'required': 'required',
                    'pattern': r'^[0-9+\-\s().]{7,30}$',
                    'title': _('Introduce un teléfono válido.'),
                }
            ),
            'event_date': forms.DateInput(
                attrs={
                    'class': 'reservation-form__input',
                    'type': 'date',
                    'required': 'required',
                }
            ),
            'event_time': forms.TimeInput(
                attrs={
                    'class': 'reservation-form__input',
                    'type': 'time',
                    'required': 'required',
                }
            ),
            'event_location': forms.TextInput(
                attrs={
                    'class': 'reservation-form__input',
                    'placeholder': _('Hotel, villa, restaurante, finca...'),
                    'required': 'required',
                }
            ),
            'event_type': forms.TextInput(
                attrs={
                    'class': 'reservation-form__input',
                    'placeholder': _('Boda, evento privado, cumpleaños...'),
                    'required': 'required',
                }
            ),
            'guests': forms.NumberInput(
                attrs={
                    'class': 'reservation-form__input',
                    'placeholder': _('Ej: 80'),
                    'min': '1',
                    'required': 'required',
                }
            ),
            'message': forms.Textarea(
                attrs={
                    'class': 'reservation-form__textarea',
                    'placeholder': _('Cuéntanos qué tipo de música o ambiente buscas...'),
                    'rows': 5,
                    'required': 'required',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        today = timezone.localdate().isoformat()

        self.fields['event_date'].widget.attrs['min'] = today

        self.fields['preferred_format'].queryset = EventFormat.objects.filter(
            is_active=True
        ).order_by(
            'display_order',
            'id'
        )

        self.fields['preferred_musician'].queryset = Musician.objects.filter(
            is_active=True
        ).order_by(
            'display_order',
            'id'
        )

        for field_name, field in self.fields.items():
            if field_name != 'website':
                field.required = True

        self.fields['website'].required = False

    def clean_client_phone(self):
        phone = self.cleaned_data.get('client_phone', '').strip()

        if not phone:
            raise ValidationError(_('El teléfono es obligatorio.'))

        allowed_characters = set('0123456789 +-.()')

        for character in phone:
            if character not in allowed_characters:
                raise ValidationError(
                    _('El teléfono solo puede contener números, espacios y los símbolos + - . ( ).')
                )

        digit_count = 0

        for character in phone:
            if character.isdigit():
                digit_count += 1

        if digit_count < 7:
            raise ValidationError(_('El teléfono debe tener al menos 7 números.'))

        if digit_count > 15:
            raise ValidationError(_('El teléfono no puede tener más de 15 números.'))

        return phone

    def clean_client_email(self):
        email = self.cleaned_data.get('client_email', '').strip()

        if not email:
            raise ValidationError(_('El email es obligatorio.'))

        return email

    def clean_event_date(self):
        event_date = self.cleaned_data.get('event_date')

        if event_date and event_date < timezone.localdate():
            raise ValidationError(
                _('No puedes hacer una reserva para una fecha anterior a hoy.')
            )

        return event_date

    def clean_guests(self):
        guests = self.cleaned_data.get('guests')

        if guests is None:
            raise ValidationError(_('El número de invitados es obligatorio.'))

        if guests < 1:
            raise ValidationError(_('El número de invitados debe ser mayor que 0.'))

        return guests

    def clean(self):
        cleaned_data = super().clean()

        website = cleaned_data.get('website', '').strip()

        if website:
            raise ValidationError(_('No se pudo enviar la reserva.'))

        return cleaned_data