import logging
import os
import textwrap
import uuid
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.shortcuts import redirect, render
from django.utils import timezone, translation
from django.utils.translation import gettext as _

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from musicians.models import Musician

from .forms import ReservationForm
from .models import AboutImage, EventFormat, HeroImage, MusicTrack, SiteConfiguration


logger = logging.getLogger(__name__)


def get_selected_language(request):
    selected_language = getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE)
    available_languages = [language_code for language_code, language_name in settings.LANGUAGES]

    if selected_language not in available_languages:
        selected_language = settings.LANGUAGE_CODE

    return selected_language


def set_language_cookie(response, language_code):
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        language_code,
        max_age=settings.LANGUAGE_COOKIE_AGE,
        samesite=getattr(settings, 'LANGUAGE_COOKIE_SAMESITE', 'Lax')
    )

    return response


def get_reservation_value(value, fallback=None):
    if fallback is None:
        fallback = _('No indicado')

    if value:
        return value

    return fallback


def build_reservation_text(reservation, config):
    event_time = _('No indicada')

    if reservation.event_time:
        event_time = reservation.event_time.strftime('%H:%M')

    guests = _('No indicado')

    if reservation.guests:
        guests = str(reservation.guests)

    preferred_format = _('No indicado')

    if reservation.preferred_format:
        preferred_format = reservation.preferred_format.translated_title

    preferred_musician = _('No indicado')

    if reservation.preferred_musician:
        preferred_musician = reservation.preferred_musician.name

    message = reservation.message or _('Sin mensaje adicional')

    return [
        _('Hola %(client_name)s,') % {
            'client_name': reservation.client_name
        },
        '',
        _('Hemos recibido correctamente tu solicitud de reserva.'),
        '',
        _('En breves nos pondremos en contacto contigo.'),
        '',
        _('Resumen de la reserva:'),
        '',
        _('Nombre: %(client_name)s') % {
            'client_name': reservation.client_name
        },
        _('Email: %(client_email)s') % {
            'client_email': reservation.client_email
        },
        _('Teléfono: %(client_phone)s') % {
            'client_phone': get_reservation_value(reservation.client_phone)
        },
        '',
        _('Fecha del evento: %(event_date)s') % {
            'event_date': reservation.event_date.strftime('%d/%m/%Y')
        },
        _('Hora aproximada: %(event_time)s') % {
            'event_time': event_time
        },
        _('Lugar del evento: %(event_location)s') % {
            'event_location': get_reservation_value(reservation.event_location)
        },
        _('Tipo de evento: %(event_type)s') % {
            'event_type': get_reservation_value(reservation.event_type)
        },
        _('Número de invitados: %(guests)s') % {
            'guests': guests
        },
        '',
        _('Formato preferido: %(preferred_format)s') % {
            'preferred_format': preferred_format
        },
        _('Músico preferido: %(preferred_musician)s') % {
            'preferred_musician': preferred_musician
        },
        '',
        _('Mensaje:'),
        message,
        '',
        _('Gracias por contactar con %(site_name)s.') % {
            'site_name': config.site_name
        },
        '',
        _('Un saludo,'),
        config.site_name,
    ]


def draw_cover_image(pdf, image_path, page_width, page_height):
    image_reader = ImageReader(image_path)
    image_width, image_height = image_reader.getSize()

    image_ratio = image_width / image_height
    page_ratio = page_width / page_height

    if image_ratio > page_ratio:
        draw_height = page_height
        draw_width = page_height * image_ratio
        x = (page_width - draw_width) / 2
        y = 0
    else:
        draw_width = page_width
        draw_height = page_width / image_ratio
        x = 0
        y = (page_height - draw_height) / 2

    pdf.drawImage(
        image_reader,
        x,
        y,
        width=draw_width,
        height=draw_height,
        preserveAspectRatio=True,
        mask='auto'
    )


def draw_pdf_background(pdf, background_image, page_width, page_height):
    if background_image and background_image.image:
        try:
            if os.path.exists(background_image.image.path):
                draw_cover_image(
                    pdf,
                    background_image.image.path,
                    page_width,
                    page_height
                )
        except Exception:
            logger.exception('No se pudo dibujar la imagen de fondo del PDF.')

    pdf.saveState()

    try:
        pdf.setFillAlpha(0.86)
    except Exception:
        pass

    pdf.setFillColorRGB(1, 1, 1)
    pdf.rect(
        1.3 * cm,
        1.3 * cm,
        page_width - 2.6 * cm,
        page_height - 2.6 * cm,
        fill=True,
        stroke=False
    )

    pdf.restoreState()


def draw_pdf_logo(pdf, config, x, y):
    if not config.logo:
        return y

    try:
        if not os.path.exists(config.logo.path):
            return y

        logo_reader = ImageReader(config.logo.path)
        logo_width, logo_height = logo_reader.getSize()

        max_width = 4.2 * cm
        max_height = 2.2 * cm

        logo_ratio = logo_width / logo_height

        if logo_ratio >= 1:
            draw_width = max_width
            draw_height = max_width / logo_ratio
        else:
            draw_height = max_height
            draw_width = max_height * logo_ratio

        pdf.drawImage(
            logo_reader,
            x,
            y - draw_height,
            width=draw_width,
            height=draw_height,
            preserveAspectRatio=True,
            mask='auto'
        )

        return y - draw_height - 0.8 * cm

    except Exception:
        logger.exception('No se pudo dibujar el logo en el PDF.')
        return y


def draw_wrapped_line(pdf, text, x, y, max_chars=92, line_height=0.48 * cm):
    if text == '':
        return y - line_height

    wrapped_lines = textwrap.wrap(text, width=max_chars)

    if not wrapped_lines:
        return y - line_height

    for wrapped_line in wrapped_lines:
        pdf.drawString(x, y, wrapped_line)
        y -= line_height

    return y


def generate_reservation_pdf(reservation, config, background_image=None):
    buffer = BytesIO()

    pdf = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4

    pdf.setTitle(
        _('Reserva - %(client_name)s') % {
            'client_name': reservation.client_name
        }
    )

    margin_x = 2 * cm
    y = page_height - 2 * cm

    draw_pdf_background(
        pdf,
        background_image,
        page_width,
        page_height
    )

    y = draw_pdf_logo(
        pdf,
        config,
        margin_x,
        y
    )

    pdf.setFont('Helvetica-Bold', 18)
    pdf.drawString(margin_x, y, config.site_name)

    y -= 0.85 * cm

    pdf.setFont('Helvetica-Bold', 14)
    pdf.drawString(
        margin_x,
        y,
        _('Confirmación de solicitud de reserva')
    )

    y -= 1 * cm

    lines = build_reservation_text(reservation, config)

    for line in lines:
        if y <= 2.3 * cm:
            pdf.showPage()

            draw_pdf_background(
                pdf,
                background_image,
                page_width,
                page_height
            )

            y = page_height - 2 * cm

            pdf.setFont('Helvetica-Bold', 12)
            pdf.drawString(margin_x, y, config.site_name)

            y -= 1 * cm

        if line in [_('Resumen de la reserva:'), _('Mensaje:')]:
            pdf.setFont('Helvetica-Bold', 10)
            y = draw_wrapped_line(pdf, line, margin_x, y)
            pdf.setFont('Helvetica', 10)
        elif line.startswith(_('En breves nos pondremos en contacto contigo.')):
            pdf.setFont('Helvetica-Bold', 11)
            y = draw_wrapped_line(pdf, line, margin_x, y)
            pdf.setFont('Helvetica', 10)
        else:
            pdf.setFont('Helvetica', 10)
            y = draw_wrapped_line(pdf, line, margin_x, y)

    pdf.save()
    buffer.seek(0)

    return buffer


def save_reservation_pdf(reservation, config, background_image=None):
    pdf_buffer = generate_reservation_pdf(
        reservation,
        config,
        background_image
    )

    folder_path = os.path.join(settings.BASE_DIR, 'private', 'reservas')
    os.makedirs(folder_path, exist_ok=True)

    filename = f'reserva-{reservation.id}-{uuid.uuid4().hex}.pdf'
    file_path = os.path.join(folder_path, filename)

    with open(file_path, 'wb') as pdf_file:
        pdf_file.write(pdf_buffer.getvalue())

    return file_path, filename


def send_reservation_email_with_pdf(
    reservation,
    config,
    background_image=None,
    language_code=None
):
    if language_code is None:
        language_code = settings.LANGUAGE_CODE

    with translation.override(language_code):
        subject = _('Solicitud de reserva recibida - %(site_name)s') % {
            'site_name': config.site_name
        }

        body = (
            _('Hola %(client_name)s,') % {
                'client_name': reservation.client_name
            }
            + '\n\n'
            + _('Hemos recibido correctamente tu solicitud de reserva.')
            + '\n\n'
            + _('En breves nos pondremos en contacto contigo.')
            + '\n\n'
            + _('Te adjuntamos un PDF con el resumen de tu reserva.')
            + '\n\n'
            + _('Un saludo,')
            + f'\n{config.site_name}'
        )

        file_path, filename = save_reservation_pdf(
            reservation,
            config,
            background_image
        )

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[reservation.client_email],
    )

    with open(file_path, 'rb') as pdf_file:
        email.attach(
            filename,
            pdf_file.read(),
            'application/pdf'
        )

    email.send(fail_silently=False)


def home(request):
    selected_language = get_selected_language(request)

    config = SiteConfiguration.get_solo()

    musicians = Musician.objects.filter(
        is_active=True
    ).order_by(
        'display_order',
        'id'
    )

    formats = EventFormat.objects.filter(
        is_active=True
    ).order_by(
        'display_order',
        'id'
    )

    hero_images = HeroImage.objects.filter(
        is_active=True
    ).order_by(
        'display_order',
        'id'
    )

    about_images = AboutImage.objects.filter(
        is_active=True
    ).order_by(
        'display_order',
        'id'
    )

    music_tracks = MusicTrack.objects.filter(
        is_active=True
    ).order_by(
        'display_order',
        'id'
    )

    background_image = hero_images.first()

    if request.method == 'POST':
        reservation_form = ReservationForm(request.POST)

        if reservation_form.is_valid():
            reservation = reservation_form.save()

            try:
                send_reservation_email_with_pdf(
                    reservation,
                    config,
                    background_image,
                    selected_language
                )

                messages.success(
                    request,
                    _('Tu solicitud de reserva se ha enviado correctamente. Te hemos enviado un email con el resumen en PDF.')
                )

            except Exception:
                logger.exception('No se pudo enviar el email con el PDF de la reserva.')

                messages.success(
                    request,
                    _('Tu solicitud de reserva se ha enviado correctamente. Te contactaremos lo antes posible.')
                )

                messages.warning(
                    request,
                    _('La reserva se ha guardado, pero no se pudo enviar el email con el PDF.')
                )

            response = redirect('home')
            return set_language_cookie(response, selected_language)
    else:
        reservation_form = ReservationForm()

    formats_payload = []

    for index, event_format in enumerate(formats, start=1):
        formats_payload.append(
            {
                'label': _('Formato %(number)s') % {
                    'number': f'{index:02d}'
                },
                'title': event_format.translated_title,
                'description': event_format.translated_description,
                'image': event_format.image.url if event_format.image else '',
                'alt': _('Formato %(title)s') % {
                    'title': event_format.translated_title
                },
            }
        )

    hero_images_payload = []

    for hero_image in hero_images:
        hero_images_payload.append(
            {
                'image': hero_image.image.url,
                'alt': hero_image.title or config.site_name,
            }
        )

    about_images_payload = []

    for about_image in about_images:
        about_images_payload.append(
            {
                'image': about_image.image.url,
                'alt': getattr(about_image, 'title', '') or config.translated_about_title or config.site_name,
            }
        )

    response = render(
        request,
        'core/home.html',
        {
            'config': config,
            'musicians': musicians,
            'formats': formats,
            'formats_payload': formats_payload,
            'hero_images': hero_images,
            'hero_images_payload': hero_images_payload,
            'about_images': about_images,
            'about_images_payload': about_images_payload,
            'music_tracks': music_tracks,
            'reservation_form': reservation_form,
            'current_year': timezone.now().year,
        }
    )

    return set_language_cookie(response, selected_language)