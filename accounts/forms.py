from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.files.uploadedfile import UploadedFile
from PIL import Image

from .models import User, Profile


class RegistrationForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email


class ProfileEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)

    class Meta:
        model = Profile
        fields = ("bio", "website", "profile_picture")
        widgets = {
            "bio": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Tell people a little about yourself..."
            }),
            "website": forms.URLInput(attrs={
                "placeholder": "https://yourwebsite.com"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["first_name"].initial = self.instance.user.first_name
        self.fields["last_name"].initial = self.instance.user.last_name

    def clean_profile_picture(self):
        image = self.cleaned_data.get("profile_picture")

        if not isinstance(image, UploadedFile):
            return image

        if image.size > 5 * 1024 * 1024:
            raise forms.ValidationError(
                "Profile picture must be smaller than 5 MB."
            )

        try:
            image.seek(0)
            with Image.open(image) as img:
                if img.format not in ("JPEG", "PNG", "WEBP"):
                    raise forms.ValidationError(
                        "Only JPG, PNG and WEBP images are allowed."
                    )
                img.verify()
        except forms.ValidationError:
            raise
        except Exception:
            raise forms.ValidationError(
                "Please upload a valid image file."
            )
        finally:
            image.seek(0)

        return image

    def save(self, commit=True):
        profile = super().save(commit=False)

        profile.user.first_name = self.cleaned_data["first_name"]
        profile.user.last_name = self.cleaned_data["last_name"]

        if commit:
            profile.save()
            profile.user.save(update_fields=["first_name", "last_name"])

        return profile