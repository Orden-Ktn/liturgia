from django.urls import path
from . import views

urlpatterns = [
    path('', views.intentions, name='intentions'),
    path('ajouter_intention/', views.ajouter_intention, name='ajouter_intention'),
    path('update_intention/<int:id>/', views.modifier_intention, name='update_intention'),
    path('delete_intention/<int:id>/', views.supprimer_intention, name='delete_intention'),

    path('autres_messes/', views.autres_messes, name='autres_messes'),
    path('ajouter_autre_messe/', views.ajouter_autre_messe, name='ajouter_autre_messe'),
    path('update_autre_messe/<int:id>/', views.modifier_autre_messe, name='update_autre_messe'),
    path('delete_autre_messe/<int:id>/', views.supprimer_autre_messe, name='delete_autre_messe'),

    path('autres_frais/', views.autres_frais, name='autres_frais'),
    path('ajouter_autre_frais/', views.ajouter_autre_frais, name='ajouter_autre_frais'),
    path('update_autre_frais/<int:id>/', views.modifier_autre_frais, name='update_autre_frais'),
    path('delete_autre_frais/<int:id>/', views.supprimer_autre_frais, name='delete_autre_frais'),

    path('liste_demandes_faites/', views.liste_demandes_faites, name='liste_demandes_faites'),

    path('pdf/', views.export_intentions_pdf, name='export_intentions_pdf'),
    path('pdf/demain/', views.export_intentions_pdf_demain, name='export_intentions_pdf_demain'),
    path('intentions/pdf/jour/', views.export_intentions_pdf_jour, name='export_intentions_pdf_jour'),
]