from django.urls import path
from . import views

urlpatterns = [
    path('', views.intentions, name='intentions'),
    path('ajouter_intention/', views.ajouter_intention, name='ajouter_intention'),
    path('update_intention/<int:id>/', views.modifier_intention, name='update_intention'),
    path('delete_intention/<int:id>/', views.supprimer_intention, name='delete_intention'),
    path('pdf/', views.export_intentions_pdf, name='export_intentions_pdf'),
    path('pdf/demain/', views.export_intentions_pdf_demain, name='export_intentions_pdf_demain'),
    path('intentions/pdf/jour/', views.export_intentions_pdf_jour, name='export_intentions_pdf_jour'),
]