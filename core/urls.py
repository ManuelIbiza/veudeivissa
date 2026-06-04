from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('reservation-pdf/', views.reservation_pdf_preview, name='reservation_pdf_preview'),
]