from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.models import CustomUser
from intentions.models import AutreFrais, Intention, MesseSpeciale
from messes.models import HoraireMesse
from .models import *
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.contrib.auth import logout, update_session_auth_hash
from django.db.models import Count, Sum
from django.utils.timezone import now
from collections import OrderedDict
from django.db.models import Sum
from django.utils import timezone


today = now().date()

@login_required
def dashboard(request):
    user = request.user

    # STATISTIQUES
    total_messes = HoraireMesse.objects.count()
    total_intentions = Intention.objects.count()
    total_autre_messe = MesseSpeciale.objects.count()

    # mois courant
    intentions_ce_mois = Intention.objects.filter(
        date_debut__year=today.year,
        date_debut__month=today.month
    ).count()

    autre_messe_ce_mois = MesseSpeciale.objects.filter(
        created_at__year=today.year,
        created_at__month=today.month
    ).count()

    # DERNIÈRES DEMANDES
    dernieres_intentions = Intention.objects.select_related(
        "demandeur", "horaire"
    ).filter(
        statut='validee'
    ).order_by("-created_at")[:10]

    context = {
        "total_messes": total_messes,
        "total_intentions": total_intentions,
        'total_autre_messe': total_autre_messe,
        "intentions_ce_mois": intentions_ce_mois,
        "dernieres_intentions": dernieres_intentions,
        "autre_messe_ce_mois": autre_messe_ce_mois,
    }

    return render(request, "dashboard.html", context)



@login_required
def finance(request):
    today = timezone.now().date()

    # Intentions de messe simples 
    montant_intention_total = Intention.objects.filter(
        statut='validee'
    ).aggregate(
        total=Sum("montant")
    )["total"] or 0

    montant_intention_ce_mois = Intention.objects.filter(
        date_debut__year=today.year,
        date_debut__month=today.month
    ).filter(statut='validee').aggregate(total=Sum("montant"))["total"] or 0

    # Autres messes (MesseSpeciale) 
    montant_autre_messe_total = MesseSpeciale.objects.aggregate(
        total=Sum("montant")
    )["total"] or 0

    montant_autre_messe_ce_mois = MesseSpeciale.objects.filter(
        date_evenement__year=today.year,
        date_evenement__month=today.month
    ).aggregate(total=Sum("montant"))["total"] or 0

    # Autres frais (AutreFrais) 
    def frais_total(categories):
        return AutreFrais.objects.filter(
            categorie__in=categories
        ).aggregate(total=Sum("montant"))["total"] or 0

    def frais_ce_mois(categories):
        return AutreFrais.objects.filter(
            categorie__in=categories,
            created_at__year=today.year,
            created_at__month=today.month
        ).aggregate(total=Sum("montant"))["total"] or 0

    total_denier_culte      = frais_total(['Denier de culte'])
    total_dime              = frais_total(['Dîme'])
    total_dime_ce_mois      = frais_ce_mois(['Dîme'])
    total_don               = frais_total(['Don'])
    total_don_ce_mois       = frais_ce_mois(['Don'])
    total_camera_photo      = frais_total(['Caméra', 'Photo'])

    # Totaux globaux
    total_autres_frais = AutreFrais.objects.aggregate(
        total=Sum("montant")
    )["total"] or 0

    total_autres_frais_ce_mois = AutreFrais.objects.filter(
        created_at__year=today.year,
        created_at__month=today.month
    ).aggregate(total=Sum("montant"))["total"] or 0

    montant_total    = montant_intention_total + montant_autre_messe_total + total_autres_frais
    montant_ce_mois  = montant_intention_ce_mois + montant_autre_messe_ce_mois + total_autres_frais_ce_mois

    return render(request, "finance.html", {
        # Globaux
        "montant_total":                montant_total,
        "montant_ce_mois":              montant_ce_mois,
        # Intentions simples
        "montant_intention_total":      montant_intention_total,
        "montant_intention_ce_mois":    montant_intention_ce_mois,
        # Autres messes
        "montant_autre_messe_total":    montant_autre_messe_total,
        "montant_autre_messe_ce_mois":  montant_autre_messe_ce_mois,
        # Autres frais par catégorie
        "total_denier_culte":           total_denier_culte,
        "total_dime":                   total_dime,
        "total_dime_ce_mois":           total_dime_ce_mois,
        "total_don":                    total_don,
        "total_don_ce_mois":            total_don_ce_mois,
        "total_camera_photo":           total_camera_photo,
    })

    
def deconnexion(request):
    logout(request)
    return redirect('login')


@login_required
def update_profil(request):
    if request.method == 'POST':
        username         = request.POST.get('username', '').strip()
        new_password     = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        errors = []

        if not username:
            errors.append("Le nom d'utilisateur est requis.")
        elif username != request.user.username and \
            CustomUser.objects.filter(username=username).exists():
            errors.append("Ce nom d'utilisateur est déjà pris.")

        if new_password:
            if len(new_password) < 8:
                errors.append("Le mot de passe doit contenir au moins 8 caractères.")
            elif new_password != confirm_password:
                errors.append("Les mots de passe ne correspondent pas.")

        if errors:
            # Renvoyer vers la page courante avec les erreurs
            return render(request, 'dashboard.html', {'profil_errors': errors})

        # Appliquer les modifications
        user = request.user
        user.username = username
        if new_password:
            user.set_password(new_password)
        user.save()

        if new_password:
            # Maintenir la session après changement de mot de passe
            update_session_auth_hash(request, user)

        messages.success(request, "Profil mis à jour avec succès.")
        return redirect(request.META.get('HTTP_REFERER', 'login'))

    return redirect('login')

