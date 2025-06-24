from email.policy import default
from django import forms

from .models import UserAccount


def validate_password(password: str) -> None:
    if len(password) < 8:
        raise forms.ValidationError("Password must be at least 8 characters long")
    if not any(char.isdigit() for char in password):
        raise forms.ValidationError("Password must contain at least one digit")
    if not any(char.isupper() for char in password):
        raise forms.ValidationError(
            "Password must contain at least one uppercase letter"
        )
    if not any(char.islower() for char in password):
        raise forms.ValidationError(
            "Password must contain at least one lowercase letter"
        )
    if not any(char in "!@#$%^&*()-_+=[]{}|;:,.<>?/" for char in password):
        raise forms.ValidationError(
            "Password must contain at least one special character"
        )
    return None


class UserAccountCreationForm(forms.ModelForm):
    class Meta:
        model = UserAccount
        fields = (
            "name",
            "email",
            "password",
            "timezone",
        )

    def clean_password(self) -> str:
        password = self.cleaned_data.get("password")
        validate_password(password)
        return password

    def save(self, commit: bool = True) -> UserAccount:
        user_account: UserAccount = super().save(commit=False)
        user_account.set_password(self.cleaned_data["password"])
        if commit:
            user_account.save()
        return user_account


class SignInForm(forms.Form):
    """Form for user sign in"""

    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    timezone = forms.CharField(widget=forms.HiddenInput, required=False)
