from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}), min_length=6)

    class Meta:
        model = User
        # `role` is set server-side in the view (Doctor/Patient signup pages)
        fields = ["username", "email", "password"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))
