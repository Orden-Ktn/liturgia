from django.db import models


class HoraireMesse(models.Model):
    JOUR_CHOICES = (
        (0, 'Lundi'),
        (1, 'Mardi'),
        (2, 'Mercredi'),
        (3, 'Jeudi'),
        (4, 'Vendredi'),
        (5, 'Samedi'),
        (6, 'Dimanche'),
    )

    TYPE_CHOICES = (
        ('normal', 'Normal'),
        ('special', 'Spécial'),
    )

    jour = models.IntegerField(choices=JOUR_CHOICES)
    heure = models.TimeField()

    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='normal')
    fete = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.get_jour_display()} - {self.heure}"
    

class Messe(models.Model):
    date_heure = models.DateTimeField()
    horaire = models.ForeignKey(HoraireMesse, on_delete=models.SET_NULL, null=True)

    cloturee = models.BooleanField(default=False)

    def __str__(self):
        return f"Messe du {self.date_heure}"