from django.urls import path
from . import views

urlpatterns = [
    path('', views.utilisateurs, name='users'),
    path('add/', views.ajouter_utilisateur, name='add_users'),
    path('<int:id>/delete/', views.supprimer_utilisateur, name='delete_users'),
]