from decimal import Decimal
from django.db import models


class GardeMoto(models.Model):
    date = models.DateField()
    groupe = models.CharField(max_length=100, blank=True, null=True)
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    montant_groupe = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    montant_em = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    montant_caritas = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    montant_jeunesse = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    montant_paroisse = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.groupe} - {self.date}"

    def calculer_pourcentages(self):
        if self.montant_total:
            if not isinstance(self.montant_total, Decimal):
                self.montant_total = Decimal(str(self.montant_total))

            self.montant_groupe = self.montant_total * Decimal('0.20')
            self.montant_em = self.montant_total * Decimal('0.10')
            self.montant_caritas = self.montant_total * Decimal('0.05')
            self.montant_jeunesse = self.montant_total * Decimal('0.05')
            self.montant_paroisse = self.montant_total * Decimal('0.60')

    def save(self, *args, **kwargs):
        self.calculer_pourcentages()
        super().save(*args, **kwargs)