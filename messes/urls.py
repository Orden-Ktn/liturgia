from django.urls import path
from . import views

urlpatterns = [
    path('', views.messes, name='messes'),
    path('ajouter/', views.ajouter_messe, name='ajouter_messe'),
    path('update_messe/<int:id>/', views.modifier_messe, name='update_messe'),
    path('delete_messe/<int:id>/', views.supprimer_messe, name='delete_messe'),
]