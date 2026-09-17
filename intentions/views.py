from collections import defaultdict
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from .models import AutreFrais, Intention, Demandeur, MesseSpeciale
from messes.models import HoraireMesse
from django.core.paginator import Paginator
from datetime import date, datetime, timedelta
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import Image
import os
from django.conf import settings
from django.utils import timezone


# LISTE
@login_required
def autres_messes(request):
    mois_param = request.GET.get('mois', timezone.now().strftime('%Y-%m'))

    try:
        mois_actif = datetime.strptime(mois_param, '%Y-%m').date().replace(day=1)
    except ValueError:
        mois_actif = timezone.now().date().replace(day=1)

    mois_precedent = (mois_actif - timedelta(days=1)).replace(day=1)
    mois_suivant = (mois_actif + timedelta(days=32)).replace(day=1)

    qs = MesseSpeciale.objects.filter(
        date_evenement__year=mois_actif.year,
        date_evenement__month=mois_actif.month
    ).select_related('demandeur').order_by('date_evenement')

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'autres_messes.html', {
        'messes': page_obj,
        'page_obj': page_obj,
        'mois_actif': mois_actif,
        'mois_precedent': mois_precedent,
        'mois_suivant': mois_suivant,
        'mois_param': mois_param,
        'today': timezone.now().date(),
    })


# AJOUT
@login_required
def ajouter_autre_messe(request):
    if request.method == "POST":
        nom = request.POST.get('nom', '').strip()
        telephone = request.POST.get('telephone', '').strip()
        categorie = request.POST.get('categorie', '').strip()
        date_evenement_str = request.POST.get('date_evenement', '').strip()

        if not nom or not date_evenement_str or not categorie:
            messages.error(request, "Champs obligatoires manquants")
            return redirect('autres_messes')

        try:
            date_evenement = datetime.strptime(date_evenement_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Format de date invalide")
            return redirect('autres_messes')

        demandeur = Demandeur.objects.create(nom=nom, telephone=telephone)

        # Récupérer le rôle de l'utilisateur connecté
        user = request.user
        role = getattr(user, 'role', None) or (
            'admin' if user.is_superuser else
            'staff' if user.is_staff else
            'user'
        )

        MesseSpeciale.objects.create(
            demandeur=demandeur,
            categorie=categorie,
            date_evenement=date_evenement,
            enregistre_par=user,
            role_enregistreur=role,
        )

        messages.success(request, "Demande enregistrée avec succès")
        return redirect('autres_messes')

    return redirect('autres_messes')


# MODIFIER
@login_required
def modifier_autre_messe(request, id):
    messe = get_object_or_404(MesseSpeciale, id=id)

    if request.method == "POST":
        nom = request.POST.get('nom', '').strip()
        telephone = request.POST.get('telephone', '').strip()
        categorie = request.POST.get('categorie', '').strip()
        date_evenement_str = request.POST.get('date_evenement', '').strip()

        if not date_evenement_str or not categorie:
            messages.error(request, "Champs obligatoires manquants")
            return redirect('autres_messes')

        try:
            messe.date_evenement = datetime.strptime(date_evenement_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Format de date invalide")
            return redirect('autres_messes')

        messe.categorie = categorie
        messe.demandeur.nom = nom
        messe.demandeur.telephone = telephone
        messe.demandeur.save()
        messe.save()  # recalcule le montant automatiquement

        messages.success(request, "Demande modifiée avec succès")
        return redirect('autres_messes')

    return redirect('autres_messes')


# SUPPRIMER
@login_required
def supprimer_autre_messe(request, id):
    messe = get_object_or_404(MesseSpeciale, id=id)
    messe.delete()
    messages.success(request, "Demande supprimée")
    return redirect('autres_messes')




# LISTE
@login_required
def autres_frais(request):
    mois_param = request.GET.get('mois', timezone.now().strftime('%Y-%m'))

    try:
        mois_actif = datetime.strptime(mois_param, '%Y-%m').date().replace(day=1)
    except ValueError:
        mois_actif = timezone.now().date().replace(day=1)

    mois_precedent = (mois_actif - timedelta(days=1)).replace(day=1)
    mois_suivant = (mois_actif + timedelta(days=32)).replace(day=1)

    qs = AutreFrais.objects.filter(
        created_at__year=mois_actif.year,
        created_at__month=mois_actif.month
    ).select_related('demandeur').order_by('-created_at')

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'autres_frais.html', {
        'frais': page_obj,       # ← renommé 'frais' pour clarté
        'page_obj': page_obj,
        'mois_actif': mois_actif,
        'mois_precedent': mois_precedent,
        'mois_suivant': mois_suivant,
        'mois_param': mois_param,
        'today': timezone.now().date(),
    })


# AJOUT
@login_required
def ajouter_autre_frais(request):
    if request.method == "POST":
        nom = request.POST.get('nom', '').strip()
        telephone = request.POST.get('telephone', '').strip()
        categorie = request.POST.get('categorie', '').strip()
        montant_str = request.POST.get('montant', '').strip()
        date_evenement_str = request.POST.get('date_evenement', '').strip()

        if not nom or not categorie:
            messages.error(request, "Champs obligatoires manquants")
            return redirect('autres_frais')

        CATEGORIES_AVEC_DATE = ['Caméra', 'Photo']
        CATEGORIES_AVEC_MONTANT = ['Denier de culte', 'Dîme', 'Don simple', 'Don hostie & vin']

        date_evenement = None
        montant = None

        if categorie in CATEGORIES_AVEC_DATE:
            if not date_evenement_str:
                messages.error(request, "La date est obligatoire pour cette catégorie")
                return redirect('autres_frais')
            try:
                date_evenement = datetime.strptime(date_evenement_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, "Format de date invalide")
                return redirect('autres_frais')

        if categorie in CATEGORIES_AVEC_MONTANT:
            if not montant_str:
                messages.error(request, "Le montant est obligatoire pour cette catégorie")
                return redirect('autres_frais')
            try:
                montant = float(montant_str)
            except ValueError:
                messages.error(request, "Montant invalide")
                return redirect('autres_frais')

        user = request.user
        role = getattr(user, 'role', None) or (
            'admin' if user.is_superuser else
            'staff' if user.is_staff else
            'user'
        )

        demandeur = Demandeur.objects.create(nom=nom, telephone=telephone)

        frais = AutreFrais(
            demandeur=demandeur,
            categorie=categorie,
            date_evenement=date_evenement,
            montant=montant,
            enregistre_par=user,
            role_enregistreur=role,
        )
        frais.save()

        messages.success(request, "Enregistré avec succès")
        return redirect('autres_frais')

    return redirect('autres_frais')


# MODIFIER
@login_required
def modifier_autre_frais(request, id):
    frais = get_object_or_404(AutreFrais, id=id)

    if request.method == "POST":
        nom = request.POST.get('nom', '').strip()
        telephone = request.POST.get('telephone', '').strip()
        categorie = request.POST.get('categorie', '').strip()
        montant_str = request.POST.get('montant', '').strip()
        date_evenement_str = request.POST.get('date_evenement', '').strip()

        if not categorie:
            messages.error(request, "La catégorie est obligatoire")
            return redirect('autres_frais')

        CATEGORIES_AVEC_DATE = ['Caméra', 'Photo']
        CATEGORIES_AVEC_MONTANT = ['Denier de culte', 'Dîme', 'Don simple', 'Don hostie & vin']

        frais.date_evenement = None
        frais.montant = None

        if categorie in CATEGORIES_AVEC_DATE:
            if not date_evenement_str:
                messages.error(request, "La date est obligatoire pour cette catégorie")
                return redirect('autres_frais')
            try:
                frais.date_evenement = datetime.strptime(date_evenement_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, "Format de date invalide")
                return redirect('autres_frais')

        if categorie in CATEGORIES_AVEC_MONTANT:
            if not montant_str:
                messages.error(request, "Le montant est obligatoire pour cette catégorie")
                return redirect('autres_frais')
            try:
                frais.montant = float(montant_str)
            except ValueError:
                messages.error(request, "Montant invalide")
                return redirect('autres_frais')

        frais.categorie = categorie
        frais.demandeur.nom = nom
        frais.demandeur.telephone = telephone
        frais.demandeur.save()
        frais.save()

        messages.success(request, "Modifié avec succès")
        return redirect('autres_frais')

    return redirect('autres_frais')


# SUPPRIMER
@login_required
def supprimer_autre_frais(request, id):
    frais = get_object_or_404(AutreFrais, id=id)
    frais.delete()
    messages.success(request, "Supprimé avec succès")
    return redirect('autres_frais')




@login_required
def intentions(request):
    today = now().date()

    # Récupération des paramètres de filtrage
    mois_param = request.GET.get('mois')   # format : "2025-01"
    page_param = request.GET.get('page', 1)

    # Mois courant par défaut
    if mois_param:
        try:
            annee, mois = int(mois_param.split('-')[0]), int(mois_param.split('-')[1])
        except (ValueError, IndexError):
            annee, mois = today.year, today.month
    else:
        annee, mois = today.year, today.month

    mois_actif = date(annee, mois, 1)

    # Filtrage des intentions sur le mois sélectionné
    qs = (
        Intention.objects
        .select_related('demandeur', 'horaire')
        .filter(Q(statut='validee') | Q(statut_paiement='paye'), date_debut__year=annee, date_debut__month=mois)
        .order_by('date_debut', 'horaire__heure')
    )

    # Pagination — 15 par page
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(page_param)

    # Navigation mois précédent / suivant
    if mois == 1:
        mois_precedent = date(annee - 1, 12, 1)
    else:
        mois_precedent = date(annee, mois - 1, 1)

    if mois == 12:
        mois_suivant = date(annee + 1, 1, 1)
    else:
        mois_suivant = date(annee, mois + 1, 1)

    messes = HoraireMesse.objects.all().order_by('jour', 'heure')

    return render(request, 'demandes.html', {
        'intentions':     page_obj,
        'page_obj':       page_obj,
        'messes':         messes,
        'today':          today,
        'mois_actif':     mois_actif,
        'mois_precedent': mois_precedent,
        'mois_suivant':   mois_suivant,
        'mois_param':     mois_actif.strftime('%Y-%m'),
    })


# AJOUT
@login_required
def ajouter_intention(request):
    if request.method == "POST":
        nom = request.POST.get('nom', '').strip()
        telephone = request.POST.get('telephone')
        categorie = request.POST.get('categorie')
        intention_text = request.POST.get('intention')
        date_debut_str = request.POST.get('date_debut')
        date_fin_str = request.POST.get('date_fin')
        horaire_id = request.POST.get('horaire_id')

        if not nom:
            nom = 'anonyme'

        if not intention_text or not date_debut_str:
            messages.error(request, "Champs obligatoires manquants")
            return redirect('intentions')
        

        demandeur = Demandeur.objects.create(
            nom=nom,
            telephone=telephone
        )

        if not horaire_id or not str(horaire_id).isdigit():
            messages.error(request, "Veuillez sélectionner un horaire de messe.")
            return redirect('intentions')

        try:
            date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date()
            date_fin = None
            if date_fin_str:
                date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Format de date invalide")
            return redirect('intentions')


        horaire = get_object_or_404(HoraireMesse, id=horaire_id)

        # Récupérer le rôle de l'utilisateur connecté
        user = request.user
        role = getattr(user, 'role', None) or (
            'admin' if user.is_superuser else
            'staff' if user.is_staff else
            'user'
        )

        # une intention = une messe
        nombre = 1

        # ✅ PLUS BESOIN de calculer le montant ici - sera fait automatiquement par save()
        intention = Intention(
            demandeur=demandeur,
            intention=intention_text,
            categorie=categorie,
            nombre=nombre,
            date_debut=date_debut,
            date_fin=date_fin if date_fin else None,
            horaire=horaire,
            role_enregistreur=role,
            statut='validee',
        )
        intention.save()  # Le montant est calculé ici

        messages.success(request, "Demande enregistrée avec succès")
        return redirect('intentions')

    return redirect('messes')


# MODIFIER
@login_required
def modifier_intention(request, id):
    intention = get_object_or_404(Intention, id=id)

    if request.method == "POST":
        intention.intention = request.POST.get('intention')
        intention.nombre = 1
        intention.categorie = request.POST.get('categorie')
        date_debut_str = request.POST.get('date_debut')
        date_fin_str = request.POST.get('date_fin')

        if not date_debut_str:
            messages.error(request, "La date est obligatoire")
            return redirect('intentions')

        try:
            if date_debut_str:
                intention.date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date()
            if date_fin_str:
                intention.date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Format de date invalide")
            return redirect('intentions')
        
        # Gestion de l'horaire
        horaire_id = request.POST.get('horaire_id')
        if horaire_id:
            horaire = get_object_or_404(HoraireMesse, id=horaire_id)
            intention.horaire = horaire
        
        # Mettre à jour le demandeur
        intention.demandeur.nom = request.POST.get('nom')
        intention.demandeur.telephone = request.POST.get('telephone')
        intention.demandeur.save()

        # ✅ PLUS BESOIN de calculer le montant - sera fait automatiquement par save()
        intention.save()  # Le montant est recalculé ici

        messages.success(request, "Demande modifiée")
        return redirect('intentions')

    return redirect('intentions')


# SUPPRIMER
@login_required
def supprimer_intention(request, id):
    intention = get_object_or_404(Intention, id=id)
    intention.delete()

    messages.success(request, "Demande supprimée")
    return redirect('intentions')


@login_required
def liste_demandes_faites(request):
    demandes = Intention.objects.filter(statut_paiement='paye').select_related('demandeur', 'horaire').order_by('-created_at')
    return render(request, 'demandes_en_ligne.html', {'demandes': demandes})



#  Couleurs

VERT      = colors.HexColor("#3a7d44")
GRIS      = colors.HexColor("#f5f5f5")
GRIS_BORD = colors.HexColor("#cccccc")
ROUGE     = colors.HexColor("#c62828")
BLEU      = colors.HexColor("#1565c0")
VIOLET    = colors.HexColor("#6a1e77")
GRIS_BLEU = colors.HexColor("#546e7a")
TEXTE     = colors.HexColor("#212121")
BLANC     = colors.white
JOUR_BG   = colors.HexColor("#2e2e2e")

CAT_COLORS = {
    "Action de grâce": BLEU,
    "Défunts":         VIOLET,
    "Autres":          ROUGE,
}

JOURS_FR = {
    0: "Lundi", 1: "Mardi", 2: "Mercredi", 3: "Jeudi",
    4: "Vendredi", 5: "Samedi", 6: "Dimanche"
}

MOIS_FR = {
    1: "Janvier", 2: "Février",  3: "Mars",     4: "Avril",
    5: "Mai",     6: "Juin",     7: "Juillet",   8: "Août",
    9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
}


#  Chemins logos

_BASE       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_GAUCHE = os.path.join(_BASE, 'static', 'images', 'logo_archidiocese.png')
LOGO_DROIT  = os.path.join(_BASE, 'static', 'images', 'sainte_bernadette.png')



#  Styles

def _get_styles():
    return {
        'titre': ParagraphStyle(
            'titre', fontSize=18, fontName='Helvetica-Bold',
            textColor=VERT, alignment=TA_CENTER, spaceAfter=4,
        ),
        'sous_titre': ParagraphStyle(
            'sousTitre', fontSize=11, fontName='Helvetica',
            textColor=colors.HexColor("#555555"), alignment=TA_CENTER, spaceAfter=2,
        ),
        'jour': ParagraphStyle(
            'jour', fontSize=13, fontName='Helvetica-Bold',
            textColor=JOUR_BG, alignment=TA_LEFT, leftIndent=0, spaceAfter=2, leading=17,
        ),
        'horaire': ParagraphStyle(
            'horaire', fontSize=11, fontName='Helvetica-Bold',
            textColor=GRIS_BLEU, alignment=TA_LEFT, leftIndent=10, spaceAfter=2, leading=15,
        ),
        'cell': ParagraphStyle(
            'cell', fontSize=13, fontName='Helvetica', textColor=TEXTE, leading=14,
        ),
        'cell_bold': ParagraphStyle(
            'cellBold', fontSize=11, fontName='Helvetica-Bold', textColor=TEXTE, leading=14,
        ),
        'footer': ParagraphStyle(
            'footer', fontSize=10, fontName='Helvetica',
            textColor=colors.HexColor("#999999"), alignment=TA_CENTER,
        ),
        'diocese': ParagraphStyle(
            'diocese', fontSize=10, fontName='Helvetica',
            textColor=colors.HexColor("#555555"), alignment=TA_CENTER, spaceAfter=3,
        ),
        'vicariat': ParagraphStyle(
            'vicariat', fontSize=10, fontName='Helvetica',
            textColor=colors.HexColor("#555555"), alignment=TA_CENTER, spaceAfter=3,
        ),
        'paroisse': ParagraphStyle(
            'paroisse', fontSize=11, fontName='Helvetica',
            textColor=colors.HexColor("#0A0A0A"),  alignment=TA_CENTER, spaceAfter=0,
        ),
        'vide': ParagraphStyle(
            'vide', fontSize=11, textColor=colors.grey, alignment=TA_CENTER,
        ),
    }


def _cat_style(couleur):
    """Style dynamique pour le libellé de catégorie, coloré selon la catégorie."""
    return ParagraphStyle(
        'catDyn', fontSize=10.5, fontName='Helvetica-Bold',
        textColor=couleur, alignment=TA_LEFT, leftIndent=18, spaceAfter=2, leading=14,
    )


#  Fonction centrale

def _build_pdf(response, intentions_qs, label_periode, today):
    # ── Groupement 3 niveaux ──
    # { date_debut : { horaire_obj : { categorie : [intention, ...] } } }
    groupes = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for intention in intentions_qs:
        cat = intention.categorie or "Autres"
        groupes[intention.date_debut][intention.horaire][cat].append(intention)

    doc = SimpleDocTemplate(
        response, pagesize=A4,
        topMargin=1.8*cm, bottomMargin=1.8*cm,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
    )

    s = _get_styles()
    story = []

    # ── Logo helper ──
    def _logo(path):
        if os.path.isfile(path):
            return Image(path, width=2*cm, height=2*cm,)
        return Paragraph("", s['cell'])

    # ── En-tête ──
    texte_entete = [
        Paragraph("ARCHIDIOCESE DE COTONOU",                   s['paroisse']),
        Paragraph("VICARIAT FORAIN SAINT LUC DE OUEDO",        s['paroisse']),
        Paragraph("PAROISSE SAINTE BERNADETTE SOUBIROUS DE HEVIE DODJI", s['paroisse']),
        Paragraph("Contacts : 01 61 33 33 98 / 01 68 83 63 65", s['paroisse']),
        Paragraph("Email : paroisse.stebernadettehevie@gmail.com", s['paroisse']),
    ]
    entete = Table(
        [[_logo(LOGO_GAUCHE), texte_entete, _logo(LOGO_DROIT)]],
        colWidths=[2.5*cm, doc.width - 5*cm, 2.5*cm],
    )
    entete.setStyle(TableStyle([
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN',        (0,0), (0, 0),  'LEFT'),
        ('ALIGN',        (1,0), (1, 0),  'CENTER'),
        ('ALIGN',        (2,0), (2, 0),  'RIGHT'),
        ('LEFTPADDING',  (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))

    story.append(entete)
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRIS_BORD))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"Intentions de Messe — {label_periode}", s['titre']))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=VERT))
    story.append(Spacer(1, 0.5*cm))

    if not groupes:
        story.append(Paragraph(
            "Aucune intention enregistrée pour cette période.", s['vide']
        ))
    else:
        for jour_date in sorted(groupes.keys()):
            horaires_du_jour = groupes[jour_date]   # { horaire_obj: { cat: [intentions] } }

            # Total du jour
            total_jour = sum(
                len(lst)
                for cats in horaires_du_jour.values()
                for lst in cats.values()
            )

            nom_jour = JOURS_FR.get(jour_date.weekday(), "")

            # ── Titre jour (texte coloré, sans fond) ──
            texte_jour = Paragraph(
                f"{nom_jour} {jour_date.strftime('%d/%m/%Y')}"
                f"  —  {total_jour} intention{'s' if total_jour > 1 else ''}",
                s['jour']
            )

            blocs = [
                texte_jour,
                HRFlowable(width="100%", thickness=1.2, color=JOUR_BG,
                           spaceBefore=2, spaceAfter=8),
            ]

            # ── Trier les horaires par heure ──
            def _heure_sort(h):
                return str(h.heure) if h and h.heure else "99:99"

            for horaire_obj in sorted(horaires_du_jour.keys(), key=_heure_sort):
                cats_de_cet_horaire = horaires_du_jour[horaire_obj]

                total_horaire = sum(len(lst) for lst in cats_de_cet_horaire.values())

                heure_label = (
                    str(horaire_obj.heure)[:5]   # "06:30"
                    if horaire_obj and horaire_obj.heure else "—"
                )

                # ── Titre horaire (texte coloré, sans fond) ──
                texte_horaire = Paragraph(
                    f"{heure_label}  —  {total_horaire} intention{'s' if total_horaire > 1 else ''}",
                    s['horaire']
                )
                blocs.append(texte_horaire)
                blocs.append(Spacer(1, 0.15*cm))

                # ── Pour chaque catégorie dans cet horaire ──
                for cat in sorted(cats_de_cet_horaire.keys()):
                    items       = cats_de_cet_horaire[cat]
                    couleur_cat = CAT_COLORS.get(cat, VERT)

                    

                    # Tableau des intentions
                    col_widths_tableau = [doc.width]

                    for i in items:
                        if i.categorie == "Action de grâce":
                            table_data = [[
                                Paragraph('<b>ACTION DE GRÂCE</b>', s['cell_bold']),
                            ]]

                        elif i.categorie == "Défunts":
                            table_data = [[
                                Paragraph('<b>DEFUNT</b>', s['cell_bold']),
                            ]]

                        else:
                            table_data = [[
                                Paragraph('<b>INTENTION(S)</b>', s['cell_bold']),
                            ]]


                    for i in items:
                        if i.categorie == "Action de grâce":
                            table_data.append([
                                
                                Paragraph("Messe d'action de grâce en l'honneur de " + i.intention  or "—", s['cell']),
                            ])
                        elif i.categorie == "Défunts":
                            table_data.append([
                                
                                Paragraph("Messe pour le repos de l'âme de " + i.intention  or "—", s['cell']),
                            ])

                        else:
                            table_data.append([
                                
                                Paragraph(i.intention  or "—", s['cell']),
                            ])

                    tableau = Table(table_data, colWidths=col_widths_tableau, repeatRows=1)

                    tableau.setStyle(TableStyle([
                        ('BACKGROUND',     (0,0),(-1,0),  GRIS),
                        ('BOTTOMPADDING',  (0,0),(-1,0),  6),
                        ('TOPPADDING',     (0,0),(-1,0),  6),
                        ('ROWBACKGROUNDS', (0,1),(-1,-1), [BLANC, GRIS]),
                        ('TOPPADDING',     (0,1),(-1,-1), 5),
                        ('BOTTOMPADDING',  (0,1),(-1,-1), 5),
                        ('LEFTPADDING',    (0,0),(-1,-1), 6),
                        ('RIGHTPADDING',   (0,0),(-1,-1), 6),
                        ('VALIGN',         (0,0),(-1,-1), 'TOP'),
                        ('GRID',           (0,0),(-1,-1), 0.4, GRIS_BORD),
                        ('LINEBELOW',      (0,0),(-1,0),  1,   couleur_cat),
                    ]))
                    blocs.append(tableau)
                    blocs.append(Spacer(1, 0.25*cm))

            story.append(KeepTogether(blocs))
            story.append(Spacer(1, 0.7*cm))

    # ── Pied de page ──
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRIS_BORD))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f"Liturgia · {today.strftime('%d/%m/%Y')}",
        s['footer']
    ))

    doc.build(story)

#  Vues

@login_required
def export_intentions_pdf(request):
    """Export du mois complet filtré."""
    today = now().date()
    mois_param = request.GET.get('mois')
    if mois_param:
        try:
            annee = int(mois_param.split('-')[0])
            mois  = int(mois_param.split('-')[1])
        except (ValueError, IndexError):
            annee, mois = today.year, today.month
    else:
        annee, mois = today.year, today.month

    label = f"{MOIS_FR[mois]} {annee}".capitalize()
    qs = (
        Intention.objects
        .select_related('demandeur', 'horaire')
        .filter(date_debut__year=annee, date_debut__month=mois)
        .order_by('date_debut', 'horaire__heure', 'categorie')
    )

    filename = f"intentions_{annee}_{mois:02d}.pdf"
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    _build_pdf(response, qs, label, today)
    return response


@login_required
def export_intentions_pdf_jour(request):
    """Export d'un jour précis via ?date=YYYY-MM-DD (aujourd'hui par défaut)."""
    today = now().date()
    date_param = request.GET.get('date')
    if date_param:
        try:
            jour_cible = date.fromisoformat(date_param)
        except ValueError:
            jour_cible = today
    else:
        jour_cible = today

    label = f"{JOURS_FR[jour_cible.weekday()]} {jour_cible.strftime('%d')} {MOIS_FR[jour_cible.month]} {jour_cible.year}".capitalize()
    qs = (
        Intention.objects
        .select_related('demandeur', 'horaire')
        .filter(date_debut=jour_cible)
        .order_by('horaire__heure', 'categorie')
    )

    filename = f"intentions_{jour_cible.strftime('%Y_%m_%d')}.pdf"
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    _build_pdf(response, qs, label, today)
    return response


@login_required
def export_intentions_pdf_demain(request):
    """Export du jour suivant."""
    demain = now().date() + timedelta(days=1)
    request.GET = request.GET.copy()
    request.GET['date'] = demain.isoformat()
    return export_intentions_pdf_jour(request)
