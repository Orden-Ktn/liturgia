from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from .models import HoraireMesse


# LISTE DES MESSES
@login_required
def messes(request):
    qs = HoraireMesse.objects.all().order_by('jour', 'heure')

    paginator = Paginator(qs, 6)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'messe.html', {'page_obj': page_obj})


# AJOUT
@login_required
def ajouter_messe(request):
    if request.method == "POST":
        jour = request.POST.get('jour')
        heure = request.POST.get('heure')
        type_messe = request.POST.get('type')
        fete = request.POST.get('fete')

        if HoraireMesse.objects.filter(jour=jour, heure=heure).exists():
            messages.error(request, "Cette messe existe déjà.")
            return redirect('messes')

        if not jour or not heure:
            messages.error(request, "Tous les champs obligatoires doivent être remplis.")
            return redirect('messes')

        HoraireMesse.objects.create(
            jour=jour,
            heure=heure,
            type=type_messe,
            fete=fete if fete else None
        )

        messages.success(request, "Messe ajoutée avec succès.")
        return redirect('messes')

    return redirect('messes')


# MODIFICATION
@login_required
def modifier_messe(request, id):
    messe = get_object_or_404(HoraireMesse, id=id)

    if request.method == "POST":
        messe.jour = request.POST.get('jour')
        messe.heure = request.POST.get('heure')
        messe.type = request.POST.get('type')
        messe.fete = request.POST.get('fete')

        messe.save()

        messages.success(request, "Messe modifiée avec succès.")
        return redirect('messes')

    return redirect('messes')


# SUPPRESSION
@login_required
def supprimer_messe(request, id):
    messe = get_object_or_404(HoraireMesse, id=id)
    messe.delete()

    messages.success(request, "Messe supprimée avec succès.")
    return redirect('messes')