from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import CustomUserCreationForm, LoginForm

User = get_user_model()



# INSCRIPTION

def register(request):
    form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})


def check_register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Compte créé avec succès.")
            return redirect('login')
        else:
            messages.error(request, "Erreur lors de l'inscription.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})



# LOGIN

def login(request):
    form = LoginForm()
    return render(request, 'login.html', {'form': form})


def check_login(request):
    form = LoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')  # adapte selon ton projet
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect")

    return render(request, 'login.html', {'form': form})



# LOGOUT

@login_required
def logout(request):
    logout(request)
    messages.success(request, "Déconnexion réussie.")
    return redirect('login')



# DASHBOARD (exemple)

@login_required
def dashboard(request):
    return render(request, 'dashboard/index.html')