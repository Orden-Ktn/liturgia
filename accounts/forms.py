from django import forms
from .models import CustomUser


class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(),
        min_length=8
    )
    role = forms.ChoiceField(
        label="Rôle",
        choices=[('vicaire', 'Vicaire'), ('secretaire', 'Secrétaire'), ('stagiaire', 'Stagiaire')]
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'role']

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur existe déjà.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    username = forms.CharField(label="Nom d'utilisateur")
    password = forms.CharField(widget=forms.PasswordInput)