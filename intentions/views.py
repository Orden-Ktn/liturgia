from collections import defaultdict
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from .models import Intention, Demandeur
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
from datetime import date, timedelta
from collections import defaultdict
from django.conf import settings



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
        .filter(date_debut__year=annee, date_debut__month=mois)
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
        nom = request.POST.get('nom')
        telephone = request.POST.get('telephone')
        categorie = request.POST.get('categorie')
        intention_text = request.POST.get('intention')
        date_debut_str = request.POST.get('date_debut')
        date_fin_str = request.POST.get('date_fin')
        horaire_id = request.POST.get('horaire_id')

        if not nom or not intention_text or not date_debut_str:
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
            # montant est omis - sera calculé automatiquement
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
        intention.date_debut_str = request.POST.get('date_debut')
        intention.date_fin_str = request.POST.get('date_fin')

        try:
            if intention.date_debut_str:
                intention.date_debut = datetime.strptime(intention.date_debut_str, '%Y-%m-%d').date()
            if intention.date_fin_str:
                intention.date_fin = datetime.strptime(intention.date_fin_str, '%Y-%m-%d').date()
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
            'jour', fontSize=11, fontName='Helvetica-Bold',
            textColor=BLANC, alignment=TA_LEFT, leftIndent=6, spaceAfter=0, leading=16,
        ),
        'horaire': ParagraphStyle(
            'horaire', fontSize=10, fontName='Helvetica-Bold',
            textColor=BLANC, alignment=TA_LEFT, leftIndent=6, spaceAfter=0, leading=14,
        ),
        'cat': ParagraphStyle(
            'cat', fontSize=9, fontName='Helvetica-Bold',
            textColor=BLANC, alignment=TA_LEFT, leftIndent=4, spaceAfter=0, leading=13,
        ),
        'cell': ParagraphStyle(
            'cell', fontSize=9, fontName='Helvetica', textColor=TEXTE, leading=12,
        ),
        'cell_bold': ParagraphStyle(
            'cellBold', fontSize=9, fontName='Helvetica-Bold', textColor=TEXTE, leading=12,
        ),
        'footer': ParagraphStyle(
            'footer', fontSize=8, fontName='Helvetica',
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
            'paroisse', fontSize=11, fontName='Helvetica-Bold',
            textColor=TEXTE, alignment=TA_CENTER, spaceAfter=0,
        ),
        'vide': ParagraphStyle(
            'vide', fontSize=11, textColor=colors.grey, alignment=TA_CENTER,
        ),
    }



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
        Paragraph("Archidiocèse de Cotonou",                   s['diocese']),
        Paragraph("Vicariat Forain Saint Luc de Ouèdo",        s['vicariat']),
        Paragraph("Paroisse Sainte Bernadette Soubirous de Hêvié Dodji", s['paroisse']),
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
        # 2 colonnes : Intention | Demandeur
        col_widths = [doc.width * 0.65, doc.width * 0.35]

        for jour_date in sorted(groupes.keys()):
            horaires_du_jour = groupes[jour_date]   # { horaire_obj: { cat: [intentions] } }

            # Total du jour
            total_jour = sum(
                len(lst)
                for cats in horaires_du_jour.values()
                for lst in cats.values()
            )

            nom_jour = JOURS_FR.get(jour_date.weekday(), "")

            # ── Bandeau jour (noir) ──
            bandeau_jour = Table(
                [[Paragraph(
                    f"  {nom_jour} {jour_date.strftime('%d/%m/%Y')}"
                    f"   —   {total_jour} intention{'s' if total_jour > 1 else ''}",
                    s['jour']
                )]],
                colWidths=[doc.width],
            )
            bandeau_jour.setStyle(TableStyle([
                ('BACKGROUND',    (0,0),(-1,-1), JOUR_BG),
                ('TOPPADDING',    (0,0),(-1,-1), 7),
                ('BOTTOMPADDING', (0,0),(-1,-1), 7),
                ('LEFTPADDING',   (0,0),(-1,-1), 8),
            ]))

            blocs = [bandeau_jour]

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

                # ── Bandeau horaire (gris-bleu) ──
                bandeau_horaire = Table(
                    [[Paragraph(
                        f"  {heure_label}"
                        f"   —   {total_horaire} intention{'s' if total_horaire > 1 else ''}",
                        s['horaire']
                    )]],
                    colWidths=[doc.width],
                )
                bandeau_horaire.setStyle(TableStyle([
                    ('BACKGROUND',    (0,0),(-1,-1), GRIS_BLEU),
                    ('TOPPADDING',    (0,0),(-1,-1), 5),
                    ('BOTTOMPADDING', (0,0),(-1,-1), 5),
                    ('LEFTPADDING',   (0,0),(-1,-1), 16),
                ]))
                blocs.append(bandeau_horaire)

                # ── Pour chaque catégorie dans cet horaire ──
                for cat in sorted(cats_de_cet_horaire.keys()):
                    items       = cats_de_cet_horaire[cat]
                    couleur_cat = CAT_COLORS.get(cat, VERT)

                    # Bandeau catégorie (coloré, indenté)
                    bandeau_cat = Table(
                        [[Paragraph(f"   {cat}  ({len(items)})", s['cat'])]],
                        colWidths=[doc.width],
                    )
                    bandeau_cat.setStyle(TableStyle([
                        ('BACKGROUND',    (0,0),(-1,-1), couleur_cat),
                        ('TOPPADDING',    (0,0),(-1,-1), 3),
                        ('BOTTOMPADDING', (0,0),(-1,-1), 3),
                        ('LEFTPADDING',   (0,0),(-1,-1), 24),
                    ]))
                    blocs.append(bandeau_cat)

                    # Tableau des intentions
                    col_widths_tableau = [doc.width * 0.20, doc.width * 0.80]

                    table_data = [[
                        Paragraph('<b>Catégorie</b>', s['cell_bold']),
                        Paragraph('<b>Intention</b>', s['cell_bold']),
                    ]]
                    for i in items:
                        table_data.append([
                            Paragraph(i.categorie or "—", s['cell']),
                            Paragraph(i.intention  or "—", s['cell']),
                        ])

                    tableau = Table(table_data, colWidths=col_widths_tableau, repeatRows=1)

                    tableau.setStyle(TableStyle([
                        ('BACKGROUND',     (0,0),(-1,0),  GRIS),
                        ('BOTTOMPADDING',  (0,0),(-1,0),  5),
                        ('TOPPADDING',     (0,0),(-1,0),  5),
                        ('ROWBACKGROUNDS', (0,1),(-1,-1), [BLANC, GRIS]),
                        ('TOPPADDING',     (0,1),(-1,-1), 4),
                        ('BOTTOMPADDING',  (0,1),(-1,-1), 4),
                        ('LEFTPADDING',    (0,0),(-1,-1), 6),
                        ('RIGHTPADDING',   (0,0),(-1,-1), 6),
                        ('VALIGN',         (0,0),(-1,-1), 'TOP'),
                        ('GRID',           (0,0),(-1,-1), 0.4, GRIS_BORD),
                        ('LINEBELOW',      (0,0),(-1,0),  1,   couleur_cat),
                    ]))
                    blocs.append(tableau)

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
