
import os

from django import forms
from django.core.files.uploadedfile import UploadedFile
from PIL import Image, UnidentifiedImageError

from .models import Post


MAX_IMAGE_SIZE = 5 * 1024 * 1024

ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

ALLOWED_IMAGE_FORMATS = {
    "JPEG",
    "PNG",
    "WEBP",
}


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ["caption", "image"]

        widgets = {
            "caption": forms.Textarea(attrs={
                "placeholder": "What's on your mind?",
                "rows": 4,
                "maxlength": 2200,
            }),
            "image": forms.ClearableFileInput(attrs={
                "accept": ".jpg,.jpeg,.png,.webp",
            }),
        }

        labels = {
            "caption": "Write a caption",
            "image": "Add a photo",
        }

    def clean_image(self):
        image = self.cleaned_data.get("image")

        # No new upload or user cleared the existing image.
        if not isinstance(image, UploadedFile):
            return image

        if image.size > MAX_IMAGE_SIZE:
            raise forms.ValidationError(
                "Image size cannot exceed 5 MB."
            )

        extension = os.path.splitext(image.name)[1].lower()

        if extension not in ALLOWED_IMAGE_EXTENSIONS:
            raise forms.ValidationError(
                "Only JPG, JPEG, PNG and WEBP images are allowed."
            )

        try:
            image.seek(0)

            with Image.open(image) as img:
                if img.format not in ALLOWED_IMAGE_FORMATS:
                    raise forms.ValidationError(
                        "Unsupported image format."
                    )

                # Prevent excessively large decoded images.
                if img.width * img.height > 25_000_000:
                    raise forms.ValidationError(
                        "Image dimensions are too large."
                    )

                img.verify()

        except forms.ValidationError:
            raise

        except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
            raise forms.ValidationError(
                "Please upload a valid image file."
            )

        finally:
            image.seek(0)

        return image

    def clean(self):
        cleaned_data = super().clean()

        caption = (cleaned_data.get("caption") or "").strip()
        image = cleaned_data.get("image")

        if not caption and not image:
            raise forms.ValidationError(
                "Please write a caption or upload an image."
            )

        return cleaned_data
