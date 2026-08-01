from django.urls import path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from . import views
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [

    path('', views.dashboard, name='dashboard'),
    path('finance/', views.finance, name='finance'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('update_profil/', views.update_profil, name='update_profil'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
