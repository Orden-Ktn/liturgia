from django.contrib import admin
from .models import HoraireMesse

@admin.register(HoraireMesse)
class HoraireMesseAdmin(admin.ModelAdmin):
    list_display = ('get_jour_display', 'heure')
    ordering = ('jour', 'heure')