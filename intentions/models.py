from datetime import datetime

from django.db import models

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

    created_at = models.DateTimeField(auto_now_add=True)

    def calculer_montant(self):
        if not self.date_debut:
            return self.nombre * 2000

        # Convertir en objet date si nécessaire
        if isinstance(self.date_debut, str):
            try:
                date_obj = datetime.strptime(self.date_debut, '%Y-%m-%d').date()
            except ValueError:
                return self.nombre * 2000
        else:
            date_obj = self.date_debut

        mois = date_obj.month

        # Novembre (11) ou Décembre (12) → tarif fixe 500
        if mois in (11, 12):
            return self.nombre * 500

        # weekday() : 0=lundi, 5=samedi, 6=dimanche
        jour = date_obj.weekday()

        # Dimanche → 2000
        if jour == 6:
            return self.nombre * 2000

        # Samedi soir 19h00 → 2000
        if jour == 5 and self.horaire:
            from datetime import time
            if self.horaire.heure == time(19, 0):
                return self.nombre * 2000

        # Jours de semaine (lundi–samedi hors 19h00) → 1200
        return self.nombre * 1200


    def save(self, *args, **kwargs):
        # Surcharge de save pour calculer automatiquement le montant
        self.montant = self.calculer_montant()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.demandeur.nom} - {self.date_debut}"