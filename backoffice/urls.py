from django.urls import path

from . import views


urlpatterns = [
    path('', views.dashboard, name='backoffice_dashboard'),

    path('hero/', views.hero_section, name='backoffice_hero_section'),
    path('about/', views.about_section, name='backoffice_about_section'),

    path('musicians/', views.musician_list, name='backoffice_musician_list'),
    path('musicians/new/', views.musician_create, name='backoffice_musician_create'),
    path('musicians/<int:musician_id>/edit/', views.musician_update, name='backoffice_musician_update'),
    path('musicians/<int:musician_id>/delete/', views.musician_delete, name='backoffice_musician_delete'),
    path('musicians/<int:musician_id>/reorder/<str:direction>/', views.musician_reorder, name='backoffice_musician_reorder'),

    path('hero-images/', views.hero_image_list, name='backoffice_hero_image_list'),
    path('hero-images/new/', views.hero_image_create, name='backoffice_hero_image_create'),
    path('hero-images/<int:hero_image_id>/edit/', views.hero_image_update, name='backoffice_hero_image_update'),
    path('hero-images/<int:hero_image_id>/delete/', views.hero_image_delete, name='backoffice_hero_image_delete'),
    path('hero-images/<int:hero_image_id>/reorder/<str:direction>/', views.hero_image_reorder, name='backoffice_hero_image_reorder'),

    path('about-images/', views.about_image_list, name='backoffice_about_image_list'),
    path('about-images/new/', views.about_image_create, name='backoffice_about_image_create'),
    path('about-images/<int:about_image_id>/edit/', views.about_image_update, name='backoffice_about_image_update'),
    path('about-images/<int:about_image_id>/delete/', views.about_image_delete, name='backoffice_about_image_delete'),
    path('about-images/<int:about_image_id>/reorder/<str:direction>/', views.about_image_reorder, name='backoffice_about_image_reorder'),

    path('formats/', views.format_list, name='backoffice_format_list'),
    path('formats/new/', views.format_create, name='backoffice_format_create'),
    path('formats/<int:format_id>/edit/', views.format_update, name='backoffice_format_update'),
    path('formats/<int:format_id>/delete/', views.format_delete, name='backoffice_format_delete'),
    path('formats/<int:format_id>/reorder/<str:direction>/', views.format_reorder, name='backoffice_format_reorder'),

    path('music/', views.music_track_list, name='backoffice_music_track_list'),
    path('music/new/', views.music_track_create, name='backoffice_music_track_create'),
    path('music/<int:music_track_id>/edit/', views.music_track_update, name='backoffice_music_track_update'),
    path('music/<int:music_track_id>/delete/', views.music_track_delete, name='backoffice_music_track_delete'),
    path('music/<int:music_track_id>/reorder/<str:direction>/', views.music_track_reorder, name='backoffice_music_track_reorder'),

    path('reservations/', views.reservation_list, name='backoffice_reservation_list'),
    path('reservations/<int:reservation_id>/edit/', views.reservation_update, name='backoffice_reservation_update'),
    path('reservations/<int:reservation_id>/delete/', views.reservation_delete, name='backoffice_reservation_delete'),

    path('site-configuration/', views.site_configuration_update, name='backoffice_site_configuration'),

    path('managers/', views.manager_list, name='backoffice_manager_list'),
    path('managers/new/', views.manager_create, name='backoffice_manager_create'),
    path('managers/<int:user_id>/edit/', views.manager_update, name='backoffice_manager_update'),
    path('managers/<int:user_id>/delete/', views.manager_delete, name='backoffice_manager_delete'),
]