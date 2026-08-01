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
import requests
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import json
import hashlib
import hmac
import unicodedata
from django.db import transaction



def _normaliser(txt):
    txt = (txt or '').strip().lower()
    txt = unicodedata.normalize('NFD', txt)
    return ''.join(c for c in txt if unicodedata.category(c) != 'Mn')


JOURS_FR = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']



def accueil(request):
    return render(request, 'accueil.html')



def demande_messe(request):
    messes = HoraireMesse.objects.all().order_by('jour', 'heure')
    return render(request, 'demande_messe.html', {'messes': messes, 'today': date.today()})



def faire_demande_messe(request):

    if request.method != "POST":
        return JsonResponse({
            'success': False,
            'error': 'Méthode non autorisée.'
        }, status=405)

    nom = request.POST.get('nom')
    telephone = request.POST.get('telephone')
    categorie = request.POST.get('categorie')
    intention_text = request.POST.get('intention')
    date_debut_str = request.POST.get('date_debut')
    horaire_id = request.POST.get('horaire_id')

    # ==============================
    # VALIDATION
    # ==============================

    if not nom or not intention_text or not date_debut_str:
        return JsonResponse({
            'success': False,
            'error': 'Champs obligatoires manquants.'
        })

    if not horaire_id or not str(horaire_id).isdigit():
        return JsonResponse({
            'success': False,
            'error': 'Veuillez sélectionner un horaire.'
        })

    try:
        date_debut = datetime.strptime(
            date_debut_str,
            '%Y-%m-%d'
        ).date()

    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'Format de date invalide.'
        })

    horaire = get_object_or_404(
        HoraireMesse,
        id=horaire_id
    )

    # ==============================
    # VERIFICATION JOUR / HORAIRE
    # ==============================

    jour_attendu = horaire.get_jour_display()
    jour_choisi = JOURS_FR[date_debut.weekday()]  # weekday(): Lundi=0 ... Dimanche=6

    if _normaliser(jour_choisi) != _normaliser(jour_attendu):
        return JsonResponse({
            'success': False,
            'error': (
                f"La date choisie tombe un {jour_choisi}, mais l'horaire "
                f"sélectionné a lieu le {jour_attendu}. Veuillez choisir "
                f"une date qui tombe un {jour_attendu}, ou changer d'horaire."
            )
        })

    # ==============================
    # VERIFICATION MESSE DEJA PASSEE
    # ==============================

    messe_datetime = datetime.combine(date_debut, horaire.heure)

    if settings.USE_TZ:
        messe_datetime = timezone.make_aware(messe_datetime)
        reference_now = timezone.now()
    else:
        reference_now = datetime.now()

    if messe_datetime <= reference_now:
        return JsonResponse({
            'success': False,
            'error': (
                "Cette messe a déjà eu lieu ou est sur le point de "
                "commencer. Veuillez choisir une date ou un horaire ultérieur."
            )
        })

    # ==============================
    # CREATION DU DEMANDEUR
    # ==============================

    demandeur = Demandeur.objects.create(
        nom=nom,
        telephone=telephone
    )

    # ==============================
    # CREATION DE L'INTENTION
    # ==============================

    intention = Intention(
        demandeur=demandeur,
        intention=intention_text,
        categorie=categorie,
        nombre=1,
        date_debut=date_debut,
        horaire=horaire,
        statut='en_attente',
        statut_paiement='en_attente',
        enregistre_par=None,
        role_enregistreur=None,
    )

    intention.save()

    # Le save() calcule automatiquement le montant
    montant = intention.montant

    # ==============================
    # REFERENCE
    # ==============================

    reference = f"LIT-{intention.id:05d}"

    # ==============================
    # URLS
    # ==============================

    return_url = request.build_absolute_uri(
        reverse(
            'paiement_leekpay_retour',
            kwargs={'id': intention.id}
        )
    )

    webhook_url = request.build_absolute_uri(
        reverse('leekpay_webhook')
    )

    # ==============================
    # CREATION CHECKOUT LEEKPAY
    # ==============================

    payload = {
        "amount": montant,
        "currency": "XOF",
        "description": f"Demande de messe {reference}",
        "return_url": return_url,
        "cancel_url": return_url,
        "webhook_url": webhook_url,

        "customer_name": nom,
        "customer_phone": telephone or "",

        "metadata": {
            "intention_id": intention.id,
            "reference": reference
        }
    }

    headers = {
        "Authorization": f"Bearer {settings.LEEKPAY_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    try:

        response = requests.post(
            f"{settings.LEEKPAY_API_URL}/checkout",
            json=payload,
            headers=headers,
            timeout=30
        )

        response_data = response.json()

    except requests.RequestException as e:

        intention.delete()

        print("ERREUR LEEKPAY :", repr(e))

        return JsonResponse({
            'success': False,
            'error': 'Impossible de contacter LeekPay.'
        })

    except ValueError:

        intention.delete()

        return JsonResponse({
            'success': False,
            'error': 'Réponse invalide de LeekPay.'
        })

    # ==============================
    # VERIFICATION REPONSE
    # ==============================

    if response.status_code not in [200, 201] or not response_data.get('success'):

        print("Erreur LeekPay :", response_data)

        intention.delete()

        return JsonResponse({
            'success': False,
            'error': 'Impossible de créer le paiement.'
        })

    checkout_data = response_data.get('data', {})

    checkout_id = checkout_data.get('id')
    payment_url = checkout_data.get('payment_url')

    if not checkout_id or not payment_url:

        intention.delete()

        return JsonResponse({
            'success': False,
            'error': 'LeekPay n’a pas retourné de lien de paiement.'
        })

    # ==============================
    # SAUVEGARDE DU CHECKOUT
    # ==============================

    intention.checkout_id = checkout_id
    intention.save(
        update_fields=['checkout_id']
    )

    # ==============================
    # INFOS MESSE
    # ==============================

    jour_display = (
        horaire.get_jour_display()
        if hasattr(horaire, 'get_jour_display')
        else str(horaire)
    )

    heure_display = (
        horaire.heure.strftime('%Hh%M')
        if horaire.heure
        else ''
    )

    # ==============================
    # REPONSE
    # ==============================

    return JsonResponse({

        'success': True,

        'payment_url': payment_url,

        'recu': {

            'reference': reference,

            'nom': nom,

            'telephone': telephone or '—',

            'categorie': categorie,

            'intention': intention_text,

            'date_messe': date_debut.strftime(
                '%d/%m/%Y'
            ),

            'horaire': (
                f'{jour_display} à {heure_display}'
            ),

            'montant': str(montant),

            'statut': 'En attente de paiement',

            'statut_paiement': 'En attente',

            'date_demande': (
                intention.created_at.strftime(
                    '%d/%m/%Y à %Hh%M'
                )
            ),
        }
    })



@csrf_exempt
def leekpay_webhook(request):

    if request.method != 'POST':
        return JsonResponse({
            'error': 'Méthode non autorisée'
        }, status=405)

    # ==============================
    # RECUPERATION DU PAYLOAD
    # ==============================

    payload = request.body

    signature = request.headers.get(
        'X-LeekPay-Signature'
    )

    if not signature:
        return JsonResponse({
            'error': 'Signature absente'
        }, status=401)

    # ==============================
    # VERIFICATION SIGNATURE
    # ==============================

    expected_signature = hmac.new(
        settings.LEEKPAY_PUBLIC_KEY.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(
        expected_signature,
        signature
    ):
        return JsonResponse({
            'error': 'Signature invalide'
        }, status=401)

    # ==============================
    # LECTURE JSON
    # ==============================

    try:
        data = json.loads(payload)

    except json.JSONDecodeError:

        return JsonResponse({
            'error': 'JSON invalide'
        }, status=400)

    event = data.get('event')

    payment_data = data.get(
        'data',
        {}
    )

    checkout_id = payment_data.get(
        'checkout_id'
    )

    transaction_id = payment_data.get(
        'transaction_id'
    )

    status = payment_data.get(
        'status'
    )

    amount = payment_data.get(
        'amount'
    )

    metadata = payment_data.get(
        'metadata'
    ) or {}

    # ==============================
    # RECUPERATION INTENTION
    # ==============================

    intention = None

    intention_id = metadata.get(
        'intention_id'
    )

    if intention_id:

        try:
            intention = Intention.objects.get(
                id=intention_id
            )

        except Intention.DoesNotExist:
            intention = None

    if intention is None and checkout_id:

        intention = Intention.objects.filter(
            checkout_id=checkout_id
        ).first()

    if intention is None:

        return JsonResponse({
            'error': 'Intention introuvable'
        }, status=404)

    # ==============================
    # VERIFICATION MONTANT
    # ==============================

    try:
        amount = int(amount)

    except (TypeError, ValueError):

        return JsonResponse({
            'error': 'Montant invalide'
        }, status=400)

    if amount != intention.montant:

        return JsonResponse({
            'error': 'Montant incorrect'
        }, status=400)

    # ==============================
    # TRAITEMENT
    # ==============================

    with transaction.atomic():

        intention.transaction_id = transaction_id
        intention.checkout_id = checkout_id

        if status == 'paid':

            intention.statut_paiement = 'paye'

            intention.date_paiement = timezone.now()

        elif status == 'failed':

            intention.statut_paiement = 'echoue'

        elif status == 'cancelled':

            intention.statut_paiement = 'annule'

        elif status == 'expired':

            intention.statut_paiement = 'expire'

        else:

            intention.statut_paiement = 'en_attente'

        intention.save(
            update_fields=[
                'transaction_id',
                'checkout_id',
                'statut_paiement',
                'date_paiement'
            ]
        )

    return JsonResponse({
        'success': True
    })


def paiement_leekpay_retour(request, id):

    intention = get_object_or_404(
        Intention,
        id=id
    )

    # ==============================
    # VERIFICATION SERVEUR
    # ==============================

    if intention.checkout_id:

        headers = {
            "Authorization": (
                f"Bearer {settings.LEEKPAY_SECRET_KEY}"
            )
        }

        try:

            response = requests.get(
                f"{settings.LEEKPAY_API_URL}/checkout/"
                f"{intention.checkout_id}",
                headers=headers,
                timeout=30
            )

            if response.ok:

                data = response.json()

                checkout_data = data.get(
                    'data',
                    {}
                )

                status = checkout_data.get(
                    'status'
                )

                if status == 'paid':

                    intention.statut_paiement = 'paye'
                    intention.statut = 'validee'

                    intention.date_paiement = (
                        timezone.now()
                    )

                    intention.transaction_id = (
                        checkout_data.get(
                            'transaction_id',
                            intention.transaction_id
                        )
                    )

                    intention.save(
                        update_fields=[
                            'transaction_id',
                            'checkout_id',
                            'statut_paiement',
                            'statut',                         
                            'date_paiement'
                        ]
                    )

        except requests.RequestException:
            pass

    return render(
        request,
        'paiement_retour.html',
        {
            'intention': intention
        }
    )