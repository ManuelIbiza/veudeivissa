from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from core.models import (
    AboutImage,
    EventFormat,
    HeroImage,
    MusicTrack,
    Reservation,
    SiteConfiguration,
)
from musicians.models import Musician

from .forms import (
    AboutContentForm,
    AboutImageForm,
    BackofficeUserCreateForm,
    BackofficeUserUpdateForm,
    EventFormatForm,
    HeroContentForm,
    HeroImageForm,
    MusicianBasicForm,
    MusicianForm,
    MusicTrackForm,
    ReservationBackofficeForm,
    SiteConfigurationForm,
)
from .models import BackofficeUserProfile


GESTOR_GROUP_NAME = 'Gestor'


# '''Función auxiliar ensure_manager_group. Crea o recupera el grupo de usuarios gestores del backoffice.'''
def ensure_manager_group():
    group, _ = Group.objects.get_or_create(name=GESTOR_GROUP_NAME)
    return group


# '''Función auxiliar get_backoffice_profile. Crea o recupera el perfil de permisos asociado a un usuario.'''
def get_backoffice_profile(user):
    profile, _ = BackofficeUserProfile.objects.get_or_create(user=user)
    return profile


# '''Función auxiliar is_backoffice_user. Comprueba si un usuario tiene acceso permitido al backoffice.'''
def is_backoffice_user(user):
    return user.is_authenticated and user.is_active and (
        user.is_superuser or user.groups.filter(name=GESTOR_GROUP_NAME).exists()
    )


# '''Función auxiliar is_superadmin. Comprueba si el usuario es un superadministrador activo.'''
def is_superadmin(user):
    return user.is_authenticated and user.is_active and user.is_superuser


# '''Función auxiliar can_manage_musicians. Comprueba si el usuario puede crear, editar, eliminar o reordenar músicos.'''
def can_manage_musicians(user):
    if user.is_superuser:
        return True

    profile = get_backoffice_profile(user)
    return profile.can_manage_musicians


# '''Función auxiliar can_manage_site_sections. Comprueba si el usuario puede editar las secciones generales de la web.'''
def can_manage_site_sections(user):
    if user.is_superuser:
        return True

    profile = get_backoffice_profile(user)
    return profile.can_manage_site_sections


# '''Función auxiliar render_backoffice_partial. Renderiza una vista parcial si la petición es AJAX o el dashboard completo si no lo es.'''
def render_backoffice_partial(request, template_name, context=None):
    context = context or {}

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(
            request,
            'backoffice/partials/_partial_wrapper.html',
            {
                'partial_template': template_name,
                **context,
            }
        )

    return render(
        request,
        'backoffice/dashboard.html',
        {
            'initial_partial': template_name,
            **context,
        }
    )


# '''Función auxiliar reorder_ordered_model_item. Intercambia la posición de un objeto ordenable con el elemento anterior o siguiente.'''
def reorder_ordered_model_item(model, object_id, direction):
    with transaction.atomic():
        ordered_items = list(
            model.objects.select_for_update().order_by('display_order', 'id')
        )

        current_index = None

        for index, item in enumerate(ordered_items):
            if item.id == object_id:
                current_index = index
                break

        if current_index is None:
            return False

        if direction == 'up':
            target_index = current_index - 1
        elif direction == 'down':
            target_index = current_index + 1
        else:
            return False

        if target_index < 0 or target_index >= len(ordered_items):
            return False

        ordered_items[current_index], ordered_items[target_index] = (
            ordered_items[target_index],
            ordered_items[current_index],
        )

        for index, item in enumerate(ordered_items, start=1):
            if item.display_order != index:
                item.display_order = index
                item.save(update_fields=['display_order'])

    return True


# '''Clase BackofficeLoginView. Gestiona el inicio de sesión específico del backoffice.'''
class BackofficeLoginView(LoginView):
    template_name = 'backoffice/registration/login.html'
    redirect_authenticated_user = True

    # '''Método get_success_url. Decide a qué página redirigir al usuario después de iniciar sesión.'''
    def get_success_url(self):
        user = self.request.user

        if is_backoffice_user(user):
            return reverse_lazy('backoffice_dashboard')

        return reverse_lazy('home')


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista dashboard. Muestra la pantalla inicial del backoffice según los permisos del usuario.'''
def dashboard(request):
    if can_manage_site_sections(request.user):
        config = SiteConfiguration.get_solo()
        hero_images = HeroImage.objects.all().order_by('display_order', 'id')

        return render(
            request,
            'backoffice/dashboard.html',
            {
                'initial_partial': 'backoffice/partials/hero_section.html',
                'config': config,
                'form': HeroContentForm(instance=config),
                'hero_images': hero_images,
            }
        )

    musicians = Musician.objects.all().order_by('display_order', 'id')

    return render(
        request,
        'backoffice/dashboard.html',
        {
            'initial_partial': 'backoffice/partials/musician_list.html',
            'musicians': musicians,
            'user_can_manage_musicians': can_manage_musicians(request.user),
        }
    )


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista musician_list. Muestra el listado de músicos dentro del backoffice.'''
def musician_list(request):
    musicians = Musician.objects.all().order_by('display_order', 'id')

    return render_backoffice_partial(
        request,
        'backoffice/partials/musician_list.html',
        {
            'musicians': musicians,
            'user_can_manage_musicians': can_manage_musicians(request.user),
        }
    )


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista musician_create. Permite crear un nuevo músico desde el backoffice.'''
def musician_create(request):
    if not can_manage_musicians(request.user):
        messages.error(request, 'No tienes permiso para crear músicos.')
        return redirect('backoffice_musician_list')

    if request.method == 'POST':
        form = MusicianForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, 'Músico creado correctamente.')
            return redirect('backoffice_musician_list')

        messages.error(request, 'No se pudo crear el músico. Revisa los campos marcados.')
    else:
        form = MusicianForm()

    return render_backoffice_partial(
        request,
        'backoffice/partials/musician_form.html',
        {
            'form': form,
            'form_title': 'Nuevo músico',
            'form_action': reverse_lazy('backoffice_musician_create'),
            'user_can_manage_musicians': True,
        }
    )


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista musician_update. Permite editar los datos de un músico existente.'''
def musician_update(request, musician_id):
    musician = get_object_or_404(Musician, id=musician_id)
    user_can_manage_musicians = can_manage_musicians(request.user)
    form_class = MusicianForm if user_can_manage_musicians else MusicianBasicForm

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=musician)

        if form.is_valid():
            form.save()
            messages.success(request, 'Músico actualizado correctamente.')
            return redirect('backoffice_musician_list')

        messages.error(request, 'No se pudo actualizar el músico. Revisa los campos marcados.')
    else:
        form = form_class(instance=musician)

    return render_backoffice_partial(
        request,
        'backoffice/partials/musician_form.html',
        {
            'form': form,
            'form_title': 'Editar músico',
            'musician': musician,
            'form_action': reverse_lazy('backoffice_musician_update', args=[musician.id]),
            'user_can_manage_musicians': user_can_manage_musicians,
        }
    )


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista musician_delete. Elimina un músico si el usuario tiene permisos para hacerlo.'''
def musician_delete(request, musician_id):
    if not can_manage_musicians(request.user):
        messages.error(request, 'No tienes permiso para eliminar músicos.')
        return redirect('backoffice_musician_list')

    musician = get_object_or_404(Musician, id=musician_id)

    if request.method == 'POST':
        musician.delete()
        messages.success(request, 'Músico eliminado correctamente.')
    else:
        messages.error(request, 'No se pudo eliminar el músico.')

    return redirect('backoffice_musician_list')


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista musician_reorder. Cambia la posición de un músico en el listado.'''
def musician_reorder(request, musician_id, direction):
    if not can_manage_musicians(request.user):
        messages.error(request, 'No tienes permiso para reordenar músicos.')
        return redirect('backoffice_musician_list')

    if request.method != 'POST':
        messages.error(request, 'No se pudo reordenar el músico.')
        return redirect('backoffice_musician_list')

    moved = reorder_ordered_model_item(Musician, musician_id, direction)

    if moved:
        messages.success(request, 'Músico reordenado correctamente.')
    else:
        messages.info(request, 'El músico ya está en esa posición.')

    return redirect('backoffice_musician_list')


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista hero_section. Muestra y procesa la edición del contenido principal del hero.'''
def hero_section(request):
    if not can_manage_site_sections(request.user):
        messages.error(request, 'No tienes permiso para editar esta sección.')
        return redirect('backoffice_musician_list')

    config = SiteConfiguration.get_solo()

    if request.method == 'POST':
        form = HeroContentForm(request.POST, instance=config)

        if form.is_valid():
            form.save()
            messages.success(request, 'Hero actualizado correctamente.')
            return redirect('backoffice_hero_section')

        messages.error(request, 'No se pudo guardar el hero. Revisa los campos marcados.')
    else:
        form = HeroContentForm(instance=config)

    hero_images = HeroImage.objects.all().order_by('display_order', 'id')

    return render_backoffice_partial(
        request,
        'backoffice/partials/hero_section.html',
        {
            'config': config,
            'form': form,
            'hero_images': hero_images,
        }
    )


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista about_section. Muestra y procesa la edición de la sección About.'''
def about_section(request):
    if not can_manage_site_sections(request.user):
        messages.error(request, 'No tienes permiso para editar esta sección.')
        return redirect('backoffice_musician_list')

    config = SiteConfiguration.get_solo()

    if request.method == 'POST':
        form = AboutContentForm(request.POST, instance=config)

        if form.is_valid():
            form.save()
            messages.success(request, 'About actualizado correctamente.')
            return redirect('backoffice_about_section')

        messages.error(request, 'No se pudo guardar el about. Revisa los campos marcados.')
    else:
        form = AboutContentForm(instance=config)

    about_images = AboutImage.objects.all().order_by('display_order', 'id')

    return render_backoffice_partial(
        request,
        'backoffice/partials/about_section.html',
        {
            'config': config,
            'form': form,
            'about_images': about_images,
        }
    )


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista hero_image_list. Devuelve la sección del hero donde se gestionan sus imágenes.'''
def hero_image_list(request):
    return hero_section(request)


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista hero_image_create. Permite añadir una nueva imagen al hero.'''
def hero_image_create(request):
    if not can_manage_site_sections(request.user):
        messages.error(request, 'No tienes permiso para crear imágenes hero.')
        return redirect('backoffice_musician_list')

    if request.method == 'POST':
        form = HeroImageForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, 'Imagen hero creada correctamente.')
            return redirect('backoffice_hero_section')

        messages.error(request, 'No se pudo crear la imagen hero. Revisa los campos marcados.')
    else:
        form = HeroImageForm()

    return render_backoffice_partial(
        request,
        'backoffice/partials/hero_image_form.html',
        {
            'form': form,
            'form_title': 'Nueva imagen hero',
            'form_action': reverse_lazy('backoffice_hero_image_create'),
        }
    )


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista hero_image_update. Permite editar una imagen existente del hero.'''
def hero_image_update(request, hero_image_id):
    if not can_manage_site_sections(request.user):
        messages.error(request, 'No tienes permiso para editar imágenes hero.')
        return redirect('backoffice_musician_list')

    hero_image = get_object_or_404(HeroImage, id=hero_image_id)

    if request.method == 'POST':
        form = HeroImageForm(request.POST, request.FILES, instance=hero_image)

        if form.is_valid():
            form.save()
            messages.success(request, 'Imagen hero actualizada correctamente.')
            return redirect('backoffice_hero_section')

        messages.error(request, 'No se pudo actualizar la imagen hero. Revisa los campos marcados.')
    else:
        form = HeroImageForm(instance=hero_image)

    return render_backoffice_partial(
        request,
        'backoffice/partials/hero_image_form.html',
        {
            'form': form,
            'form_title': 'Editar imagen hero',
            'hero_image': hero_image,
            'form_action': reverse_lazy('backoffice_hero_image_update', args=[hero_image.id]),
        }
    )


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista hero_image_delete. Elimina una imagen del hero.'''
def hero_image_delete(request, hero_image_id):
    if not can_manage_site_sections(request.user):
        messages.error(request, 'No tienes permiso para eliminar imágenes hero.')
        return redirect('backoffice_musician_list')

    hero_image = get_object_or_404(HeroImage, id=hero_image_id)

    if request.method == 'POST':
        hero_image.delete()
        messages.success(request, 'Imagen hero eliminada correctamente.')
    else:
        messages.error(request, 'No se pudo eliminar la imagen hero.')

    return redirect('backoffice_hero_section')


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista hero_image_reorder. Cambia la posición de una imagen del hero.'''
def hero_image_reorder(request, hero_image_id, direction):
    if not can_manage_site_sections(request.user):
        messages.error(request, 'No tienes permiso para reordenar imágenes hero.')
        return redirect('backoffice_hero_section')

    if request.method != 'POST':
        messages.error(request, 'No se pudo reordenar el/la imagen hero.')
        return redirect('backoffice_hero_section')

    moved = reorder_ordered_model_item(HeroImage, hero_image_id, direction)

    if moved:
        messages.success(request, 'Imagen hero reordenado/a correctamente.')
    else:
        messages.info(request, 'El/la imagen hero ya está en esa posición.')

    return redirect('backoffice_hero_section')


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista about_image_list. Devuelve la sección About donde se gestionan sus imágenes.'''
def about_image_list(request):
    return about_section(request)


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista about_image_create. Permite añadir una nueva imagen a la sección About.'''
def about_image_create(request):
    if not can_manage_site_sections(request.user):
        messages.error(request, 'No tienes permiso para crear imágenes about.')
        return redirect('backoffice_musician_list')

    if request.method == 'POST':
        form = AboutImageForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, 'Imagen about creada correctamente.')
            return redirect('backoffice_about_section')

        messages.error(request, 'No se pudo crear la imagen about. Revisa los campos marcados.')
    else:
        form = AboutImageForm()

    return render_backoffice_partial(
        request,
        'backoffice/partials/about_image_form.html',
        {
            'form': form,
            'form_title': 'Nueva imagen about',
            'form_action': reverse_lazy('backoffice_about_image_create'),
        }
    )


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista about_image_update. Permite editar una imagen existente de la sección About.'''
def about_image_update(request, about_image_id):
    if not can_manage_site_sections(request.user):
        messages.error(request, 'No tienes permiso para editar imágenes about.')
        return redirect('backoffice_musician_list')

    about_image = get_object_or_404(AboutImage, id=about_image_id)

    if request.method == 'POST':
        form = AboutImageForm(request.POST, request.FILES, instance=about_image)

        if form.is_valid():
            form.save()
            messages.success(request, 'Imagen about actualizada correctamente.')
            return redirect('backoffice_about_section')

        messages.error(request, 'No se pudo actualizar la imagen about. Revisa los campos marcados.')
    else:
        form = AboutImageForm(instance=about_image)

    return render_backoffice_partial(
        request,
        'backoffice/partials/about_image_form.html',
        {
            'form': form,
            'form_title': 'Editar imagen about',
            'about_image': about_image,
            'form_action': reverse_lazy('backoffice_about_image_update', args=[about_image.id]),
        }
    )


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista about_image_delete. Elimina una imagen de la sección About.'''
def about_image_delete(request, about_image_id):
    if not can_manage_site_sections(request.user):
        messages.error(request, 'No tienes permiso para eliminar imágenes about.')
        return redirect('backoffice_musician_list')

    about_image = get_object_or_404(AboutImage, id=about_image_id)

    if request.method == 'POST':
        about_image.delete()
        messages.success(request, 'Imagen about eliminada correctamente.')
    else:
        messages.error(request, 'No se pudo eliminar la imagen about.')

    return redirect('backoffice_about_section')


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista about_image_reorder. Cambia la posición de una imagen de la sección About.'''
def about_image_reorder(request, about_image_id, direction):
    if not can_manage_site_sections(request.user):
        messages.error(request, 'No tienes permiso para reordenar imágenes about.')
        return redirect('backoffice_about_section')

    if request.method != 'POST':
        messages.error(request, 'No se pudo reordenar el/la imagen about.')
        return redirect('backoffice_about_section')

    moved = reorder_ordered_model_item(AboutImage, about_image_id, direction)

    if moved:
        messages.success(request, 'Imagen about reordenado/a correctamente.')
    else:
        messages.info(request, 'El/la imagen about ya está en esa posición.')

    return redirect('backoffice_about_section')


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista format_list. Muestra el listado de formatos de evento en el backoffice.'''
def format_list(request):
    if not can_manage_site_sections(request.user):
        messages.error(request, 'No tienes permiso para editar esta sección.')
        return redirect('backoffice_musician_list')

    formats = EventFormat.objects.all().order_by('display_order', 'id')

    return render_backoffice_partial(
        request,
        'backoffice/partials/format_list.html',
        {
            'formats': formats,
        }
    )


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista format_create. Permite crear un nuevo formato de evento.'''
def format_create(request):
    if not can_manage_site_sections(request.user):
        messages.error(request, 'No tienes permiso para crear formatos.')
        return redirect('backoffice_musician_list')

    if request.method == 'POST':
        form = EventFormatForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, 'Formato creado correctamente.')
            return redirect('backoffice_format_list')

        messages.error(request, 'No se pudo crear el formato. Revisa los campos marcados.')
    else:
        form = EventFormatForm()

    return render_backoffice_partial(
        request,
        'backoffice/partials/format_form.html',
        {
            'form': form,
            'form_title': 'Nuevo formato',
            'form_action': reverse_lazy('backoffice_format_create'),
        }
    )


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista format_update. Permite editar un formato de evento existente.'''
def format_update(request, format_id):
    if not can_manage_site_sections(request.user):
        messages.error(request, 'No tienes permiso para editar formatos.')
        return redirect('backoffice_musician_list')

    event_format = get_object_or_404(EventFormat, id=format_id)

    if request.method == 'POST':
        form = EventFormatForm(request.POST, request.FILES, instance=event_format)

        if form.is_valid():
            form.save()
            messages.success(request, 'Formato actualizado correctamente.')
            return redirect('backoffice_format_list')

        messages.error(request, 'No se pudo actualizar el formato. Revisa los campos marcados.')
    else:
        form = EventFormatForm(instance=event_format)

    return render_backoffice_partial(
        request,
        'backoffice/partials/format_form.html',
        {
            'form': form,
            'form_title': 'Editar formato',
            'event_format': event_format,
            'form_action': reverse_lazy('backoffice_format_update', args=[event_format.id]),
        }
    )


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista format_delete. Elimina un formato de evento.'''
def format_delete(request, format_id):
    if not can_manage_site_sections(request.user):
        messages.error(request, 'No tienes permiso para eliminar formatos.')
        return redirect('backoffice_musician_list')

    event_format = get_object_or_404(EventFormat, id=format_id)

    if request.method == 'POST':
        event_format.delete()
        messages.success(request, 'Formato eliminado correctamente.')
    else:
        messages.error(request, 'No se pudo eliminar el formato.')

    return redirect('backoffice_format_list')


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista format_reorder. Cambia la posición de un formato dentro del listado.'''
def format_reorder(request, format_id, direction):
    if not can_manage_site_sections(request.user):
        messages.error(request, 'No tienes permiso para editar esta sección.')
        return redirect('backoffice_format_list')

    if request.method != 'POST':
        messages.error(request, 'No se pudo reordenar el/la formato.')
        return redirect('backoffice_format_list')

    moved = reorder_ordered_model_item(EventFormat, format_id, direction)

    if moved:
        messages.success(request, 'Formato reordenado/a correctamente.')
    else:
        messages.info(request, 'El/la formato ya está en esa posición.')

    return redirect('backoffice_format_list')


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista music_track_list. Muestra el listado de canciones o enlaces de Spotify.'''
def music_track_list(request):
    if not can_manage_site_sections(request.user):
        messages.error(request, 'No tienes permiso para editar esta sección.')
        return redirect('backoffice_musician_list')

    music_tracks = MusicTrack.objects.all().order_by('display_order', 'id')

    return render_backoffice_partial(
        request,
        'backoffice/partials/music_track_list.html',
        {
            'music_tracks': music_tracks,
        }
    )


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista music_track_create. Permite crear una nueva canción o enlace de Spotify.'''
def music_track_create(request):
    if not can_manage_site_sections(request.user):
        messages.error(request, 'No tienes permiso para crear canciones.')
        return redirect('backoffice_musician_list')

    if request.method == 'POST':
        form = MusicTrackForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'Canción creada correctamente.')
            return redirect('backoffice_music_track_list')

        messages.error(request, 'No se pudo crear la canción. Revisa los campos marcados.')
    else:
        form = MusicTrackForm()

    return render_backoffice_partial(
        request,
        'backoffice/partials/music_track_form.html',
        {
            'form': form,
            'form_title': 'Nueva canción',
            'form_action': reverse_lazy('backoffice_music_track_create'),
        }
    )


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista music_track_update. Permite editar una canción o enlace de Spotify existente.'''
def music_track_update(request, music_track_id):
    if not can_manage_site_sections(request.user):
        messages.error(request, 'No tienes permiso para editar canciones.')
        return redirect('backoffice_musician_list')

    music_track = get_object_or_404(MusicTrack, id=music_track_id)

    if request.method == 'POST':
        form = MusicTrackForm(request.POST, instance=music_track)

        if form.is_valid():
            form.save()
            messages.success(request, 'Canción actualizada correctamente.')
            return redirect('backoffice_music_track_list')

        messages.error(request, 'No se pudo actualizar la canción. Revisa los campos marcados.')
    else:
        form = MusicTrackForm(instance=music_track)

    return render_backoffice_partial(
        request,
        'backoffice/partials/music_track_form.html',
        {
            'form': form,
            'form_title': 'Editar canción',
            'music_track': music_track,
            'form_action': reverse_lazy('backoffice_music_track_update', args=[music_track.id]),
        }
    )


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista music_track_delete. Elimina una canción o enlace de Spotify.'''
def music_track_delete(request, music_track_id):
    if not can_manage_site_sections(request.user):
        messages.error(request, 'No tienes permiso para eliminar canciones.')
        return redirect('backoffice_musician_list')

    music_track = get_object_or_404(MusicTrack, id=music_track_id)

    if request.method == 'POST':
        music_track.delete()
        messages.success(request, 'Canción eliminada correctamente.')
    else:
        messages.error(request, 'No se pudo eliminar la canción.')

    return redirect('backoffice_music_track_list')


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista music_track_reorder. Cambia la posición de una canción dentro del listado.'''
def music_track_reorder(request, music_track_id, direction):
    if not can_manage_site_sections(request.user):
        messages.error(request, 'No tienes permiso para editar esta sección.')
        return redirect('backoffice_music_track_list')

    if request.method != 'POST':
        messages.error(request, 'No se pudo reordenar el/la canción.')
        return redirect('backoffice_music_track_list')

    moved = reorder_ordered_model_item(MusicTrack, music_track_id, direction)

    if moved:
        messages.success(request, 'Canción reordenado/a correctamente.')
    else:
        messages.info(request, 'El/la canción ya está en esa posición.')

    return redirect('backoffice_music_track_list')


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista reservation_list. Muestra el listado de reservas y sus contadores por estado.'''
def reservation_list(request):
    reservations = Reservation.objects.select_related(
        'preferred_format',
        'preferred_musician',
    ).order_by(
        '-created_at'
    )

    pending_count = reservations.filter(status=Reservation.STATUS_PENDING).count()
    confirmed_count = reservations.filter(status=Reservation.STATUS_CONFIRMED).count()
    cancelled_count = reservations.filter(status=Reservation.STATUS_CANCELLED).count()
    completed_count = reservations.filter(status=Reservation.STATUS_COMPLETED).count()

    return render_backoffice_partial(
        request,
        'backoffice/partials/reservations_list.html',
        {
            'reservations': reservations,
            'pending_count': pending_count,
            'confirmed_count': confirmed_count,
            'cancelled_count': cancelled_count,
            'completed_count': completed_count,
        }
    )


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista reservation_update. Permite gestionar y actualizar el estado o datos internos de una reserva.'''
def reservation_update(request, reservation_id):
    reservation = get_object_or_404(
        Reservation.objects.select_related(
            'preferred_format',
            'preferred_musician',
        ),
        id=reservation_id
    )

    if request.method == 'POST':
        form = ReservationBackofficeForm(request.POST, instance=reservation)

        if form.is_valid():
            form.save()
            messages.success(request, 'Reserva actualizada correctamente.')
            return redirect('backoffice_reservation_list')

        messages.error(request, 'No se pudo actualizar la reserva. Revisa los campos marcados.')
    else:
        form = ReservationBackofficeForm(instance=reservation)

    return render_backoffice_partial(
        request,
        'backoffice/partials/reservation_form.html',
        {
            'reservation': reservation,
            'form': form,
            'form_title': 'Gestionar reserva',
            'form_action': reverse_lazy('backoffice_reservation_update', args=[reservation.id]),
        }
    )


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista reservation_delete. Elimina una solicitud de reserva del sistema.'''
def reservation_delete(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)

    if request.method == 'POST':
        reservation.delete()
        messages.success(request, 'Reserva eliminada correctamente.')
    else:
        messages.error(request, 'No se pudo eliminar la reserva.')

    return redirect('backoffice_reservation_list')


@login_required
@user_passes_test(is_backoffice_user)
# '''Vista site_configuration_update. Permite editar la configuración general del sitio web.'''
def site_configuration_update(request):
    if not can_manage_site_sections(request.user):
        messages.error(request, 'No tienes permiso para editar la configuración.')
        return redirect('backoffice_musician_list')

    config = SiteConfiguration.get_solo()

    if request.method == 'POST':
        form = SiteConfigurationForm(request.POST, request.FILES, instance=config)

        if form.is_valid():
            form.save()
            messages.success(request, 'Configuración guardada correctamente.')
            return redirect('backoffice_site_configuration')

        messages.error(request, 'No se pudo guardar la configuración. Revisa los campos marcados.')
    else:
        form = SiteConfigurationForm(instance=config)

    return render_backoffice_partial(
        request,
        'backoffice/partials/site_configuration.html',
        {
            'config': config,
            'form': form,
        }
    )


@login_required
@user_passes_test(is_superadmin)
# '''Vista manager_list. Muestra los usuarios gestores y superadministradores del backoffice.'''
def manager_list(request):
    users = User.objects.filter(
        Q(is_superuser=True) | Q(groups__name=GESTOR_GROUP_NAME)
    ).order_by(
        '-is_superuser',
        'username'
    ).distinct()

    for user in users:
        get_backoffice_profile(user)

    return render_backoffice_partial(
        request,
        'backoffice/partials/manager_list.html',
        {
            'managers': users,
        }
    )


@login_required
@user_passes_test(is_superadmin)
# '''Vista manager_create. Permite crear un nuevo usuario gestor del backoffice.'''
def manager_create(request):
    ensure_manager_group()

    if request.method == 'POST':
        form = BackofficeUserCreateForm(request.POST)

        if form.is_valid():
            user = form.save()
            user.groups.clear()
            user.groups.add(ensure_manager_group())
            messages.success(request, 'Usuario creado correctamente.')
            return redirect('backoffice_manager_list')

        messages.error(request, 'No se pudo crear el usuario. Revisa los campos marcados.')
    else:
        form = BackofficeUserCreateForm()

    return render_backoffice_partial(
        request,
        'backoffice/partials/manager_form.html',
        {
            'form': form,
            'form_title': 'Nuevo usuario',
        }
    )


@login_required
@user_passes_test(is_superadmin)
# '''Vista manager_update. Permite editar los datos y permisos de un usuario gestor.'''
def manager_update(request, user_id):
    user = get_object_or_404(
        User.objects.filter(
            Q(is_superuser=True) | Q(groups__name=GESTOR_GROUP_NAME)
        ).distinct(),
        id=user_id
    )

    if request.method == 'POST':
        form = BackofficeUserUpdateForm(request.POST, instance=user)

        if form.is_valid():
            updated_user = form.save()

            if not updated_user.is_superuser:
                updated_user.groups.clear()
                updated_user.groups.add(ensure_manager_group())

            messages.success(request, 'Usuario actualizado correctamente.')
            return redirect('backoffice_manager_list')

        messages.error(request, 'No se pudo actualizar el usuario. Revisa los campos marcados.')
    else:
        form = BackofficeUserUpdateForm(instance=user)

    return render_backoffice_partial(
        request,
        'backoffice/partials/manager_form.html',
        {
            'form': form,
            'form_title': 'Editar usuario',
            'manager': user,
        }
    )


@login_required
@user_passes_test(is_superadmin)
# '''Vista manager_delete. Elimina un usuario gestor del backoffice si no es superadministrador ni el propio usuario.'''
def manager_delete(request, user_id):
    user = get_object_or_404(
        User.objects.filter(
            Q(is_superuser=True) | Q(groups__name=GESTOR_GROUP_NAME)
        ).distinct(),
        id=user_id
    )

    if user.is_superuser:
        messages.error(request, 'No se puede eliminar un superadmin.')
        return redirect('backoffice_manager_list')

    if user == request.user:
        messages.error(request, 'No puedes eliminar tu propio usuario.')
        return redirect('backoffice_manager_list')

    if request.method == 'POST':
        user.delete()
        messages.success(request, 'Usuario eliminado correctamente.')
    else:
        messages.error(request, 'No se pudo eliminar el usuario.')

    return redirect('backoffice_manager_list')