import logging
import os
import textwrap
import uuid
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.utils import timezone, translation
from django.utils.translation import gettext as _

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None
    ImageDraw = None
    ImageFont = None

from musicians.models import Musician

from .forms import ReservationForm
from .models import AboutImage, EventFormat, HeroImage, MusicTrack, SiteConfiguration


logger = logging.getLogger(__name__)

RESERVATION_PDF_SESSION_KEY = 'latest_reservation_pdf_filename'
RESERVATION_PREVIEW_SESSION_KEY = 'latest_reservation_preview_filename'


'''Función auxiliar get_selected_language. Obtiene el idioma activo de la petición y comprueba que sea uno de los idiomas disponibles.'''
def get_selected_language(request):
    selected_language = getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE)
    available_languages = [language_code for language_code, language_name in settings.LANGUAGES]

    if selected_language not in available_languages:
        selected_language = settings.LANGUAGE_CODE

    return selected_language


'''Función auxiliar set_language_cookie. Guarda el idioma seleccionado en una cookie para mantenerlo en futuras visitas.'''
def set_language_cookie(response, language_code):
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        language_code,
        max_age=settings.LANGUAGE_COOKIE_AGE,
        samesite=getattr(settings, 'LANGUAGE_COOKIE_SAMESITE', 'Lax')
    )

    return response


'''Función get_reservation_value. Devuelve el valor de un campo de reserva o un texto por defecto si está vacío.'''
def get_reservation_value(value, fallback=None):
    if fallback is None:
        fallback = _('No indicado')

    if value:
        return value

    return fallback


'''Función auxiliar get_first_hero_background. Obtiene la primera imagen activa del hero para usarla como fondo.'''
def get_first_hero_background(hero_images):
    return hero_images.first()


'''Función auxiliar get_image_bytes_from_field. Lee una imagen desde un campo ImageField y devuelve su contenido en bytes.'''
def get_image_bytes_from_field(image_field):
    if not image_field:
        return None

    try:
        if hasattr(image_field, 'path') and os.path.exists(image_field.path):
            with open(image_field.path, 'rb') as image_file:
                return image_file.read()
    except Exception:
        pass

    try:
        image_field.open('rb')
        image_bytes = image_field.read()
        image_field.close()

        return image_bytes
    except Exception:
        logger.exception('No se pudo leer la imagen desde el almacenamiento.')
        return None


'''Función auxiliar build_reservation_text. Construye el contenido textual con el resumen de una reserva.'''
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


'''Función auxiliar draw_cover_image. Dibuja una imagen cubriendo toda la página del PDF.'''
def draw_cover_image(pdf, image_source, page_width, page_height):
    if isinstance(image_source, bytes):
        image_reader = ImageReader(BytesIO(image_source))
    else:
        image_reader = ImageReader(image_source)

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


'''Función auxiliar draw_pdf_background. Dibuja el fondo del PDF y añade una capa clara para mejorar la lectura.'''
def draw_pdf_background(pdf, background_image, page_width, page_height):
    if background_image and background_image.image:
        try:
            image_bytes = get_image_bytes_from_field(background_image.image)

            if image_bytes:
                draw_cover_image(
                    pdf,
                    image_bytes,
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


'''Función auxiliar draw_pdf_logo. Dibuja el logo de la web dentro del PDF si existe.'''
def draw_pdf_logo(pdf, config, x, y):
    if not config.logo:
        return y

    try:
        logo_bytes = get_image_bytes_from_field(config.logo)

        if not logo_bytes:
            return y

        logo_reader = ImageReader(BytesIO(logo_bytes))
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


'''Función auxiliar draw_wrapped_line. Dibuja texto en el PDF dividiéndolo en varias líneas si es demasiado largo.'''
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


'''Función auxiliar generate_reservation_pdf. Genera en memoria el PDF con el resumen de una reserva.'''
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


'''Función auxiliar save_reservation_pdf. Guarda en una carpeta privada el PDF generado para una reserva.'''
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


'''Función auxiliar load_preview_font. Carga una fuente para generar la imagen de previsualización de la reserva.'''
def load_preview_font(size, bold=False):
    if ImageFont is None:
        return None

    font_candidates = []

    if bold:
        font_candidates.extend([
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf',
            'arialbd.ttf',
        ])
    else:
        font_candidates.extend([
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
            'arial.ttf',
        ])

    for font_path in font_candidates:
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            continue

    return ImageFont.load_default()


'''Función auxiliar resize_image_to_cover. Redimensiona y recorta una imagen para cubrir completamente un tamaño concreto.'''
def resize_image_to_cover(image, target_width, target_height):
    image_width, image_height = image.size
    image_ratio = image_width / image_height
    target_ratio = target_width / target_height

    if image_ratio > target_ratio:
        new_height = target_height
        new_width = int(target_height * image_ratio)
    else:
        new_width = target_width
        new_height = int(target_width / image_ratio)

    image = image.resize((new_width, new_height), Image.LANCZOS)

    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2

    return image.crop((left, top, left + target_width, top + target_height))


'''Función auxiliar draw_preview_wrapped_text. Dibuja texto en la imagen de previsualización ajustándolo al ancho disponible.'''
def draw_preview_wrapped_text(draw, text, x, y, font, fill, max_width, line_spacing=10):
    if not text:
        return y + 28

    words = str(text).split()
    lines = []
    current_line = ''

    for word in words:
        test_line = f'{current_line} {word}'.strip()
        bbox = draw.textbbox((x, y), test_line, font=font)
        line_width = bbox[2] - bbox[0]

        if line_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        bbox = draw.textbbox((x, y), line, font=font)
        y += (bbox[3] - bbox[1]) + line_spacing

    return y


'''Función auxiliar generate_reservation_preview_image. Genera una imagen PNG de previsualización con el resumen de una reserva.'''
def generate_reservation_preview_image(reservation, config, background_image=None):
    if Image is None:
        return None

    width = 1240
    height = 1754

    base = Image.new('RGB', (width, height), '#f7f2eb')

    if background_image and background_image.image:
        try:
            image_bytes = get_image_bytes_from_field(background_image.image)

            if image_bytes:
                background = Image.open(BytesIO(image_bytes)).convert('RGB')
                background = resize_image_to_cover(background, width, height)
                base.paste(background, (0, 0))
        except Exception:
            logger.exception('No se pudo dibujar la imagen de fondo de la previsualización.')

    overlay = Image.new('RGBA', (width, height), (255, 253, 250, 225))
    margin = 90
    content_box = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    content_draw = ImageDraw.Draw(content_box)
    content_draw.rounded_rectangle(
        (margin, margin, width - margin, height - margin),
        radius=28,
        fill=(255, 253, 250, 232),
        outline=(211, 197, 178, 160),
        width=2
    )
    base = Image.alpha_composite(base.convert('RGBA'), overlay)
    base = Image.alpha_composite(base, content_box)

    draw = ImageDraw.Draw(base)

    title_font = load_preview_font(48, bold=True)
    subtitle_font = load_preview_font(34, bold=True)
    body_font = load_preview_font(25)
    body_bold_font = load_preview_font(25, bold=True)
    small_font = load_preview_font(22)

    text_color = '#403a34'
    accent_color = '#a88f76'
    x = 145
    y = 140
    max_width = width - (x * 2)

    if config.logo:
        try:
            logo_bytes = get_image_bytes_from_field(config.logo)

            if logo_bytes:
                logo = Image.open(BytesIO(logo_bytes)).convert('RGBA')
                logo.thumbnail((260, 120), Image.LANCZOS)
                base.alpha_composite(logo, (x, y))
                y += logo.height + 35

        except Exception:
            logger.exception('No se pudo dibujar el logo en la previsualización.')

    draw.text((x, y), config.site_name, font=title_font, fill=text_color)
    y += 70
    draw.text((x, y), _('Confirmación de solicitud de reserva'), font=subtitle_font, fill=accent_color)
    y += 80

    lines = build_reservation_text(reservation, config)

    for line in lines:
        if line in [_('Resumen de la reserva:'), _('Mensaje:')]:
            y += 14
            y = draw_preview_wrapped_text(draw, line, x, y, body_bold_font, text_color, max_width, 13)
        elif line == '':
            y += 24
        else:
            y = draw_preview_wrapped_text(draw, line, x, y, body_font, text_color, max_width, 12)

        if y > height - 180:
            break

    draw.text(
        (x, height - 155),
        _('Documento generado automáticamente.'),
        font=small_font,
        fill=accent_color
    )

    output = BytesIO()
    base.convert('RGB').save(output, format='PNG', optimize=True)
    output.seek(0)

    return output


''' Función  auxiliar save_reservation_preview_image. Guarda en una carpeta privada la imagen de previsualización de una reserva.'''
def save_reservation_preview_image(reservation, config, background_image=None):
    preview_buffer = generate_reservation_preview_image(
        reservation,
        config,
        background_image
    )

    if preview_buffer is None:
        return None, None

    folder_path = os.path.join(settings.BASE_DIR, 'private', 'reservas')
    os.makedirs(folder_path, exist_ok=True)

    filename = f'reserva-{reservation.id}-{uuid.uuid4().hex}.png'
    file_path = os.path.join(folder_path, filename)

    with open(file_path, 'wb') as image_file:
        image_file.write(preview_buffer.getvalue())

    return file_path, filename


'''Función auxiliar send_reservation_email_with_pdf. Envía al cliente un email de confirmación con el PDF de la reserva adjunto.'''
def send_reservation_email_with_pdf(
    reservation,
    config,
    background_image=None,
    language_code=None,
    pdf_path=None,
    pdf_filename=None
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

        if pdf_path and pdf_filename:
            file_path = pdf_path
            filename = pdf_filename
        else:
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


'''Vista reservation_pdf_preview. Muestra en el navegador el último PDF de reserva guardado en la sesión.'''
def reservation_pdf_preview(request):
    filename = request.session.get(RESERVATION_PDF_SESSION_KEY)

    if not filename:
        raise Http404(_('No hay ningún PDF de reserva disponible.'))

    safe_filename = os.path.basename(filename)

    if safe_filename != filename or not safe_filename.lower().endswith('.pdf'):
        raise Http404(_('PDF no válido.'))

    file_path = os.path.join(settings.BASE_DIR, 'private', 'reservas', safe_filename)

    if not os.path.exists(file_path):
        raise Http404(_('El PDF de la reserva ya no está disponible.'))

    response = FileResponse(
        open(file_path, 'rb'),
        content_type='application/pdf'
    )
    response['Content-Disposition'] = f'inline; filename="{safe_filename}"'

    return response


'''Vista reservation_preview_image. Muestra en el navegador la última imagen de previsualización guardada en la sesión.'''
def reservation_preview_image(request):
    filename = request.session.get(RESERVATION_PREVIEW_SESSION_KEY)

    if not filename:
        raise Http404(_('No hay ninguna imagen de reserva disponible.'))

    safe_filename = os.path.basename(filename)

    if safe_filename != filename or not safe_filename.lower().endswith('.png'):
        raise Http404(_('Imagen no válida.'))

    file_path = os.path.join(settings.BASE_DIR, 'private', 'reservas', safe_filename)

    if not os.path.exists(file_path):
        raise Http404(_('La imagen de la reserva ya no está disponible.'))

    response = FileResponse(
        open(file_path, 'rb'),
        content_type='image/png'
    )
    response['Content-Disposition'] = f'inline; filename="{safe_filename}"'

    return response


'''Vista home. Muestra la página principal, carga sus datos y procesa el formulario de reserva.'''
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

    background_image = get_first_hero_background(hero_images)

    if request.method == 'POST':
        reservation_form = ReservationForm(request.POST)

        if reservation_form.is_valid():
            reservation = reservation_form.save()

            with translation.override(selected_language):
                reservation_pdf_path, reservation_pdf_filename = save_reservation_pdf(
                    reservation,
                    config,
                    background_image
                )
                reservation_preview_path, reservation_preview_filename = save_reservation_preview_image(
                    reservation,
                    config,
                    background_image
                )

            request.session[RESERVATION_PDF_SESSION_KEY] = reservation_pdf_filename

            if reservation_preview_filename:
                request.session[RESERVATION_PREVIEW_SESSION_KEY] = reservation_preview_filename
            else:
                request.session.pop(RESERVATION_PREVIEW_SESSION_KEY, None)

            try:
                send_reservation_email_with_pdf(
                    reservation,
                    config,
                    background_image,
                    selected_language,
                    reservation_pdf_path,
                    reservation_pdf_filename
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
            'reservation_pdf_available': bool(request.session.get(RESERVATION_PDF_SESSION_KEY)),
            'reservation_preview_available': bool(request.session.get(RESERVATION_PREVIEW_SESSION_KEY)),
            'current_year': timezone.now().year,
        }
    )

    return set_language_cookie(response, selected_language)