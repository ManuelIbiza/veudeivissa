from django.urls import path
from . import views

urlpatterns = [
    path('', views.musician_list, name='musician_list'),
]