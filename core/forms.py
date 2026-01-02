from django import forms
from django.contrib.auth.forms import AuthenticationForm

from django.contrib.auth.forms import UserCreationForm
from .models import User

class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'})
    )
    password = forms.CharField(
        label="Palavra-passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

class ClienteSignupForm(UserCreationForm):
    tipo_subscricao = forms.ChoiceField(choices=User.TIPO_SUBS, required=True, label="Tipo de subscrição")

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "tipo_subscricao", "password1", "password2")

class InstrutorSignupForm(UserCreationForm):
    foto_perfil = forms.ImageField(required=False, label="Foto de Perfil")

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "password1", "password2", "foto_perfil")
