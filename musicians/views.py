from django.shortcuts import render
from django.utils import timezone

from core.models import SiteConfiguration
from .models import Musician


'''Vista musician_list. Devuelve la sección con los músicos activos ordenados para la web.'''
def musician_list(request):
    config = SiteConfiguration.get_solo()

    musicians = Musician.objects.filter(
        is_active=True
    ).order_by(
        'display_order',
        'id'
    )

    return render(
        request,
        'musicians/musicians.html',
        {
            'config': config,
            'musicians': musicians,
            'current_year': timezone.now().year,
        }
    )