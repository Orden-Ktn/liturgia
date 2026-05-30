import os
from django.conf import settings
from django.utils import timezone
from collections import defaultdict
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from intentions.models import Demandeur, Intention
from messes.models import HoraireMesse
from django.core.paginator import Paginator
from datetime import date, datetime, timedelta
from django.http import HttpResponse
import json
from django.http import JsonResponse


def accueil(request):
    return render(request, 'accueil.html')



def demande_messe(request):
    messes = HoraireMesse.objects.all().order_by('jour', 'heure')
    return render(request, 'demande_messe.html', {'messes': messes, 'today': date.today()})



def faire_demande_messe(request):
    if request.method == "POST":
        nom = request.POST.get('nom')
        telephone = request.POST.get('telephone')
        categorie = request.POST.get('categorie')
        intention_text = request.POST.get('intention')
        date_debut_str = request.POST.get('date_debut')
        horaire_id = request.POST.get('horaire_id')

        if not nom or not intention_text or not date_debut_str:
            return JsonResponse({'success': False, 'error': 'Champs obligatoires manquants.'})

        if not horaire_id or not str(horaire_id).isdigit():
            return JsonResponse({'success': False, 'error': 'Veuillez sélectionner un horaire.'})

        try:
            date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Format de date invalide.'})

        horaire = get_object_or_404(HoraireMesse, id=horaire_id)

        demandeur = Demandeur.objects.create(nom=nom, telephone=telephone)

        intention = Intention(
            demandeur=demandeur,
            intention=intention_text,
            categorie=categorie,
            nombre=1,
            date_debut=date_debut,
            horaire=horaire,
            statut='en_attente',  
            enregistre_par=None,
            role_enregistreur=None,
        )
        intention.save()

        # Formater le jour de la messe
        jour_display = horaire.get_jour_display() if hasattr(horaire, 'get_jour_display') else str(horaire)
        heure_display = horaire.heure.strftime('%Hh%M') if horaire.heure else ''

        return JsonResponse({
            'success': True,
            'recu': {
                'reference': f'LIT-{intention.id:05d}',
                'nom': nom,
                'telephone': telephone or '—',
                'categorie': categorie,
                'intention': intention_text,
                'date_messe': date_debut.strftime('%d/%m/%Y'),
                'horaire': f'{jour_display} à {heure_display}',
                'montant': str(intention.montant),
                'statut': 'En attente',
                'date_demande': intention.created_at.strftime('%d/%m/%Y à %Hh%M'),
            }
        })

    return redirect('demande_messe')

