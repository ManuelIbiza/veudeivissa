"""
URL configuration for projecte_veu project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include, path

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
]


urlpatterns += i18n_patterns(
    path('', include('core.urls')),
    path('musicians/', include('musicians.urls')),
)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)