from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [

    path('demande-messe', views.demande_messe, name='demande_messe'),
    path('demande-messe/envoyer/', views.faire_demande_messe, name='faire_demande_messe'),
    
    path('', views.accueil, name='accueil'),

    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
