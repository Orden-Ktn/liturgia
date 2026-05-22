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
        """Calcule le montant basé sur la date de début"""
        # Vérifier si date_debut est une chaîne ou un objet date
        if self.date_debut:
            # Si c'est une chaîne, la convertir en objet date
            if isinstance(self.date_debut, str):
                try:
                    date_obj = datetime.strptime(self.date_debut, '%Y-%m-%d').date()
                except ValueError:
                    return self.nombre * 2000  # Valeur par défaut en cas d'erreur
            else:
                date_obj = self.date_debut
            
            mois = date_obj.month
            # Novembre (11) ou Décembre (12)
            if mois == 11 or mois == 12:
                return self.nombre * 500
        
        return self.nombre * 2000
    
    def save(self, *args, **kwargs):
        # Surcharge de save pour calculer automatiquement le montant
        self.montant = self.calculer_montant()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.demandeur.nom} - {self.date_debut}"