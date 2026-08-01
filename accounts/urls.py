from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [

    path('login/', views.login, name='login'),
    path('check_login/', views.check_login, name='check_login'),
    path('register/', views.register, name='register'),
   
    path('check_register/', views.check_register, name='check_register'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
