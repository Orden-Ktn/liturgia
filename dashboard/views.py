from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.models import CustomUser
from intentions.models import AutreFrais, Intention, MesseSpeciale
from messes.models import HoraireMesse
from .models import *
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout, update_session_auth_hash
from django.db.models import Q, Count, Sum
from django.utils.timezone import now
from collections import OrderedDict
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from decimal import Decimal, InvalidOperation


today = now().date()


def get_semaine_mercredi_mardi(d=None):
    """
    Retourne (debut_semaine, fin_semaine) où la semaine va
    du mercredi au mardi suivant (inclus), pour la date `d`.
    Si d est None, utilise la date du jour.
    """
    if d is None:
        d = timezone.localdate()

    # Mercredi = 2 dans weekday() (Lundi=0 ... Dimanche=6)
    jours_depuis_mercredi = (d.weekday() - 2) % 7
    debut_semaine = d - timedelta(days=jours_depuis_mercredi)
    fin_semaine = debut_semaine + timedelta(days=6)  # le mardi suivant

    return debut_semaine, fin_semaine


def get_stats_semaine(debut_s, fin_s, label):
    """Retourne le nombre de messes et le montant total pour une période donnée."""
    stats = Intention.objects.filter(
        date_debut__range=(debut_s, fin_s),
        statut='validee'
    ).aggregate(
        nombre_messes=Count('id'),
        montant_total=Sum('montant')
    )
    return {
        'label': label,
        'debut_semaine': debut_s,
        'fin_semaine': fin_s,
        'nombre_messes': stats['nombre_messes'] or 0,
        'montant_total': stats['montant_total'] or 0,
    }


@login_required
def dashboard(request):
    user = request.user

    # STATISTIQUES
    total_messes = HoraireMesse.objects.count()
    total_intentions_sg = Intention.objects.filter(statut='validee').count()
    total_intentions_ligne = Intention.objects.filter(statut_paiement='paye').count()
    total_autre_messe = MesseSpeciale.objects.count()

    debut_semaine, fin_semaine = get_semaine_mercredi_mardi()

    montant_messe_secretariat_cette_semaine = Intention.objects.filter(
        date_debut__range=(debut_semaine, fin_semaine),
        statut='validee'
    ).count()

    # ===== SEMAINE EN COURS + SEMAINE PRÉCÉDENTE (déjà célébrées / en cours) =====
    semaines = []
    for offset in [0, 1]:  # 0 = en cours, 1 = précédente
        date_ref = today - timedelta(weeks=offset)
        debut_s, fin_s = get_semaine_mercredi_mardi(date_ref)
        label = "Semaine en cours" if offset == 0 else "Semaine précédente"
        semaines.append(get_stats_semaine(debut_s, fin_s, label))

    # ===== 2 SEMAINES À VENIR (messes déjà payées, à célébrer plus tard) =====
    semaines_avenir = []
    for offset in [1, 2]:  # 1 = semaine prochaine, 2 = dans 2 semaines
        date_ref = today + timedelta(weeks=offset)
        debut_s, fin_s = get_semaine_mercredi_mardi(date_ref)
        label = "Semaine prochaine" if offset == 1 else "Dans 2 semaines"
        semaines_avenir.append(get_stats_semaine(debut_s, fin_s, label))

    # Montant total déjà encaissé pour les messes à venir (à remettre / reverser)
    montant_total_a_remettre = sum(s['montant_total'] for s in semaines_avenir)
    nombre_total_messes_avenir = sum(s['nombre_messes'] for s in semaines_avenir)

    # mois courant
    intentions_ce_mois = Intention.objects.filter(
        created_at__year=today.year,
        created_at__month=today.month
    ).filter(Q(statut='validee') | Q(statut_paiement='paye')).count()

    autre_messe_ce_mois = MesseSpeciale.objects.filter(
        created_at__year=today.year,
        created_at__month=today.month
    ).count()

    context = {
        "total_messes": total_messes,
        "total_intentions_sg": total_intentions_sg,
        "total_intentions_ligne": total_intentions_ligne,
        'total_autre_messe': total_autre_messe,
        "intentions_ce_mois": intentions_ce_mois,
        "autre_messe_ce_mois": autre_messe_ce_mois,
        'montant_messe_secretariat_cette_semaine': montant_messe_secretariat_cette_semaine,
        'semaines': semaines,
        'semaines_avenir': semaines_avenir,
        'montant_total_a_remettre': montant_total_a_remettre,
        'nombre_total_messes_avenir': nombre_total_messes_avenir,
    }

    return render(request, "dashboard.html", context)


@login_required
def finance(request):
    today = timezone.now().date()

    debut_semaine, fin_semaine = get_semaine_mercredi_mardi()

    # Intentions de messe simples
    montant_intention_total = Intention.objects.filter(
        statut='validee'
    ).aggregate(
        total=Sum("montant")
    )["total"] or 0

    montant_messe_cette_semaine = Intention.objects.filter(
        date_debut__range=(debut_semaine, fin_semaine),
        statut='validee'
    ).aggregate(total=Sum("montant"))["total"] or 0

    # montants messes demandees cette semaine
    montant_messe_secretariat_cette_semaine = Intention.objects.filter(
        date_debut__range=(debut_semaine, fin_semaine), statut='validee'
    ).aggregate(total=Sum("montant"))["total"] or 0

    montant_messe_en_ligne_cette_semaine = Intention.objects.filter(
        date_debut__range=(debut_semaine, fin_semaine), statut_paiement='paye'
    ).aggregate(total=Sum("montant"))["total"] or 0

    montant_messes_demandees_cette_semaine = montant_messe_secretariat_cette_semaine + montant_messe_en_ligne_cette_semaine

    # montants messes demandees ce mois
    montant_messe_secretariat_ce_mois = Intention.objects.filter(
        date_debut__year=today.year,
        date_debut__month=today.month, statut='validee'
    ).aggregate(total=Sum("montant"))["total"] or 0

    montant_messe_en_ligne_ce_mois = Intention.objects.filter(
        date_debut__year=today.year,
        date_debut__month=today.month, statut_paiement='paye'
    ).aggregate(total=Sum("montant"))["total"] or 0

    montant_messes_demandees_ce_mois = montant_messe_secretariat_ce_mois + montant_messe_en_ligne_ce_mois

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
    montant_messes_ce_mois_sans_doublon = Intention.objects.filter(
        Q(statut='validee') | Q(statut_paiement='paye'),
        date_debut__year=today.year,
        date_debut__month=today.month
    ).aggregate(total=Sum("montant"))["total"] or 0

    montant_ce_mois = montant_messes_ce_mois_sans_doublon + montant_autre_messe_ce_mois + total_autres_frais_ce_mois
    # ===== SEMAINE EN COURS + SEMAINE PRÉCÉDENTE (compte, mercredi -> mardi) =====
    semaines = []
    for offset in [0, 1]:  # 0 = en cours, 1 = précédente
        date_ref = today - timedelta(weeks=offset)
        debut_s, fin_s = get_semaine_mercredi_mardi(date_ref)
        label = "Semaine en cours" if offset == 0 else "Semaine précédente"
        semaines.append(get_stats_semaine(debut_s, fin_s, label))

    # ===== SURPLUS SUR LES SEMAINES À VENIR (messes déjà payées, à célébrer plus tard) =====
    semaines_avenir = []
    for offset in [1, 2]:  # 1 = semaine prochaine, 2 = dans 2 semaines
        date_ref = today + timedelta(weeks=offset)
        debut_s, fin_s = get_semaine_mercredi_mardi(date_ref)
        label = "Semaine prochaine" if offset == 1 else "Dans 2 semaines"
        semaines_avenir.append(get_stats_semaine(debut_s, fin_s, label))

    montant_total_a_remettre = sum(s['montant_total'] for s in semaines_avenir)
    nombre_total_messes_avenir = sum(s['nombre_messes'] for s in semaines_avenir)

    return render(request, "finance.html", {
        # Globaux
        "montant_total":                montant_total,
        "montant_ce_mois":              montant_ce_mois,
        # Intentions simples
        "montant_intention_total":      montant_intention_total,
        "montant_messe_secretariat_ce_mois":    montant_messe_secretariat_ce_mois,
        "montant_messe_en_ligne_ce_mois": montant_messe_en_ligne_ce_mois,
        "montant_messes_demandees_ce_mois": montant_messes_demandees_ce_mois,
        "montant_messe_secretariat_cette_semaine":    montant_messe_secretariat_cette_semaine,
        "montant_messe_en_ligne_cette_semaine": montant_messe_en_ligne_cette_semaine,
        "montant_messes_demandees_cette_semaine": montant_messes_demandees_cette_semaine,
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
        "montant_messe_cette_semaine":  montant_messe_cette_semaine,
        # ===== NOUVEAU : semaines actuelle/précédente + surplus à venir =====
        "semaines":                     semaines,
        "semaines_avenir":              semaines_avenir,
        "montant_total_a_remettre":     montant_total_a_remettre,
        "nombre_total_messes_avenir":   nombre_total_messes_avenir,
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



@login_required
def garde_moto(request):
    if request.method == 'POST':
        date = request.POST.get('date')
        groupe = request.POST.get('groupe')
        montant_total_raw = request.POST.get('montant_total')

        if not date or not montant_total_raw:
            messages.error(request, "La date et le montant total sont obligatoires.")
            return redirect('garde_moto')

        try:
            montant_total = Decimal(montant_total_raw)
        except InvalidOperation:
            messages.error(request, "Le montant total doit être un nombre valide.")
            return redirect('garde_moto')

        try:
            GardeMoto.objects.create(
                date=date,
                groupe=groupe,
                montant_total=montant_total,
            )
            messages.success(request, "Enregistrement effectué avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur lors de l'enregistrement : {e}")

        return redirect('garde_moto')

    qs = GardeMoto.objects.all()
    montant_total = GardeMoto.objects.aggregate(
        total=Sum("montant_total")
    )["total"] or 0
    montant_em = GardeMoto.objects.aggregate(
        total=Sum("montant_em")
    )["total"] or 0
    montant_groupe = GardeMoto.objects.aggregate(
        total=Sum("montant_groupe")
    )["total"] or 0
    montant_caritas = GardeMoto.objects.aggregate(
        total=Sum("montant_caritas")
    )["total"] or 0
    montant_jeunesse = GardeMoto.objects.aggregate(
            total=Sum("montant_jeunesse")
    )["total"] or 0
    montant_paroisse = GardeMoto.objects.aggregate(
        total=Sum("montant_paroisse")
    )["total"] or 0
    page_param = request.GET.get('page', 1)
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(page_param)

    return render(request, 'garde_moto.html', 
        {
            'page_obj': page_obj, 
            'montant_total':montant_total, 
            'montant_em':montant_em, 
            'montant_groupe':montant_groupe, 
            'montant_caritas':montant_caritas, 
            'montant_jeunesse':montant_jeunesse, 
            'montant_paroisse':montant_paroisse
        }
    )

