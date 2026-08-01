from django.contrib import admin
from .models import AutreFrais, Intention, Demandeur, MesseSpeciale

@admin.register(Intention)
class IntentionAdmin(admin.ModelAdmin):
    list_display = ('demandeur', 'categorie', 'date_debut', 'horaire', 'statut', 'montant', 'created_at', 'enregistre_par')
    list_filter = ('statut', 'categorie', 'date_debut')
    search_fields = ('demandeur__nom', 'intention')
    ordering = ('-created_at',)

@admin.register(Demandeur)
class DemandeurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'telephone')
    search_fields = ('nom',)

@admin.register(AutreFrais)
class AutreFraisAdmin(admin.ModelAdmin):
    list_display = ('demandeur', 'montant', 'created_at', 'enregistre_par', 'categorie', 'date_evenement', 'montant')
    search_fields = ('demandeur',)
    ordering = ('-created_at',)

@admin.register(MesseSpeciale)
class MesseSpecialeAdmin(admin.ModelAdmin):
    list_display = ('demandeur', 'categorie', 'date_evenement', 'montant', 'created_at', 'enregistre_par')
    search_fields = ('demandeur__nom',)
    ordering = ('-created_at',)