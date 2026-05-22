from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from accounts.models import CustomUser
from intentions.models import Intention
from messes.models import HoraireMesse

from .models import *
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.contrib.auth import logout, update_session_auth_hash
from django.db.models import Count, Sum
from django.utils.timezone import now
from collections import OrderedDict


@login_required
def dashboard(request):
    user = request.user

    # ===== STATISTIQUES =====
    total_messes = HoraireMesse.objects.count()
    total_intentions = Intention.objects.count()

    # mois courant
    today = now().date()
    intentions_ce_mois = Intention.objects.filter(
        date_debut__year=today.year,
        date_debut__month=today.month
    ).count()

    # montant total
    montant_total = Intention.objects.aggregate(
        total=Sum("montant")
    )["total"] or 0

    # montant pour le mois courant
    montant_ce_mois = Intention.objects.filter(
        date_debut__year=today.year,
        date_debut__month=today.month
    ).aggregate(total=Sum("montant"))["total"] or 0

    # ===== DERNIÈRES DEMANDES =====
    dernieres_intentions = Intention.objects.select_related(
        "demandeur", "horaire"
    ).order_by("-created_at")[:10]

    context = {
        "total_messes": total_messes,
        "total_intentions": total_intentions,
        "intentions_ce_mois": intentions_ce_mois,
        "montant_total": montant_total,
        "montant_ce_mois": montant_ce_mois,
        "dernieres_intentions": dernieres_intentions,

    }

    return render(request, "dashboard.html", context)



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

