from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.forms import CustomUserCreationForm
from accounts.models import CustomUser


@login_required
def utilisateurs(request):
    users = CustomUser.objects.exclude(is_superuser=True).exclude(role='cure').order_by('username')
    form = CustomUserCreationForm()
    return render(request, 'users.html', {'users': users, 'form': form})


@login_required
def ajouter_utilisateur(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Utilisateur « {user.username} » créé avec succès.")
            return redirect('users')
        else:
            # Renvoyer le formulaire avec les erreurs
            users = CustomUser.objects.exclude(is_superuser=True).exclude(role='cure').order_by('username')
            return render(request, 'users.html', {'users': users, 'form': form})

    return redirect('users')


@login_required
def supprimer_utilisateur(request, id):
    user = get_object_or_404(CustomUser, id=id)

    # Empêcher la suppression du curé
    if user.role == 'cure':
        messages.error(request, "Impossible de supprimer le curé.")
        return redirect('users')

    username = user.username
    user.delete()
    messages.success(request, f"Utilisateur « {username} » supprimé.")
    return redirect('users')


