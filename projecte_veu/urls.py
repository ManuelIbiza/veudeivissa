from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include, path
from django.views.generic import RedirectView

from backoffice.views import BackofficeLoginView


urlpatterns = [
    path('admin/', admin.site.urls),

    path('backoffice/', include('backoffice.urls')),

    path('login/', BackofficeLoginView.as_view(), name='login'),

    path(
        'logout/',
        LogoutView.as_view(next_page='login'),
        name='logout'
    ),

    path('', RedirectView.as_view(url='/es/', permanent=False)),
]


urlpatterns += i18n_patterns(
    path('', include('core.urls')),
    path('musicians/', include('musicians.urls')),
)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)