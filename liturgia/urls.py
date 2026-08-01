from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')), 
    path('dashboard/', include('dashboard.urls')),
    path('messes/', include('messes.urls')),
    path('intentions/', include('intentions.urls')),
    path('users/', include('users.urls')), 
    path('', include('home.urls')),  

]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
