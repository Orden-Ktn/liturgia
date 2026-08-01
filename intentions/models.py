from datetime import datetime
from django.db import models
from liturgia import settings


class Demandeur(models.Model):
    nom = models.CharField(max_length=255)
    telephone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nom



class Intention(models.Model):
    demandeur = models.ForeignKey(Demandeur, on_delete=models.CASCADE)

    intention = models.TextField()
    categorie = models.CharField(max_length=100, blank=True, null=True)
    nombre = models.PositiveIntegerField(default=1)

    date_debut = models.DateField()
    date_fin = models.DateField(blank=True, null=True)

    horaire = models.ForeignKey('messes.HoraireMesse', on_delete=models.SET_NULL, null=True)

    montant = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    statut = models.CharField(max_length=20)

    enregistre_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='intentions_enregistrees'
    )
    role_enregistreur = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    checkout_id = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        unique=True
    )

    transaction_id = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    statut_paiement = models.CharField(
        max_length=20,
        default='en_attente'
    )

    date_paiement = models.DateTimeField(
        null=True,
        blank=True
    )

    def calculer_montant(self):
        if not self.date_debut:
            return self.nombre * 100

        # Convertir en objet date si nécessaire
        if isinstance(self.date_debut, str):
            try:
                date_obj = datetime.strptime(self.date_debut, '%Y-%m-%d').date()
            except ValueError:
                return self.nombre * 100
        else:
            date_obj = self.date_debut

        mois = date_obj.month

        # Novembre (11) ou Décembre (12) → tarif fixe 500
        if mois in (11, 12):
            return self.nombre * 500

        # weekday() : 0=lundi, 5=samedi, 6=dimanche
        jour = date_obj.weekday()

        # Dimanche → 100
        if jour == 6:
            return self.nombre * 100

        # Samedi soir 19h00 → 100
        if jour == 5 and self.horaire:
            from datetime import time
            if self.horaire.heure == time(19, 0):
                return self.nombre * 100

        # Jours de semaine (lundi–samedi hors 19h00) → 100
        return self.nombre * 100


    def save(self, *args, **kwargs):
        # Surcharge de save pour calculer automatiquement le montant
        self.montant = self.calculer_montant()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.demandeur.nom} - {self.date_debut}"
    


class MesseSpeciale(models.Model):
    CATEGORIES = [
        ('Action de grâce', 'Action de grâce'),
        ('Obsèques', 'Obsèques'),
        ('Mariage', 'Mariage'),
        ('Diplôme', 'Diplôme'),
        ('Baptême bébé', 'Baptême bébé'),
    ]

    demandeur = models.ForeignKey(Demandeur, on_delete=models.CASCADE)
    categorie = models.CharField(max_length=100, choices=CATEGORIES, blank=True, null=True)
    date_evenement = models.DateField()
    montant = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    enregistre_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='messes_enregistrees'
    )
    role_enregistreur = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def calculer_montant(self):
        if self.categorie in ['Action de grâce', 'Obsèques', 'Mariage', 'Diplôme']:
            return 10000
        elif self.categorie == 'Baptême bébé':
            return 5500
        return 0

    def save(self, *args, **kwargs):
        self.montant = self.calculer_montant()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.demandeur.nom} - {self.date_evenement}"
    
    

class AutreFrais(models.Model):
    CATEGORIES = [
        ('Denier de culte', 'Denier de culte'),
        ('Dîme', 'Dîme'),
        ('Don', 'Don'),
        ('Caméra', 'Caméra'),
        ('Photo', 'Photo'),
    ]

    demandeur = models.ForeignKey(Demandeur, on_delete=models.CASCADE)
    categorie = models.CharField(max_length=100, choices=CATEGORIES, blank=True, null=True)
    date_evenement = models.DateField(blank=True, null=True)
    montant = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    enregistre_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='autres_frais_enregistres'
    )
    role_enregistreur = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    CATEGORIES_MONTANT_FIXE = ['Caméra', 'Photo']
    CATEGORIES_MONTANT_LIBRE = ['Denier de culte', 'Dîme', 'Don']

    def save(self, *args, **kwargs):
        # Caméra/Photo : montant fixe automatique, pas de date obligatoire
        if self.categorie in self.CATEGORIES_MONTANT_FIXE:
            if not self.montant:
                self.montant = 5000
        # Dîme/Don/Denier : montant libre saisi, pas de date
        # → on ne touche pas au montant
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.demandeur.nom} - {self.categorie}"

        