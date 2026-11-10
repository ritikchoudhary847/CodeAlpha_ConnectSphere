
import os

from django import forms
from .models import Message


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm"}

IMAGE_MIMES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
}

VIDEO_MIMES = {
    "video/mp4",
    "video/quicktime",
    "video/webm",
}


class MessageForm(forms.ModelForm):

    class Meta:
        model = Message
        fields = ["body", "attachment"]
        widgets = {
            "body": forms.Textarea(attrs={
                "placeholder": "Write a message...",
                "rows": 1,
                "maxlength": 5000,
            }),
            "attachment": forms.ClearableFileInput(attrs={
                "accept": (
                    "image/jpeg,image/png,image/gif,image/webp,"
                    "video/mp4,video/quicktime,video/webm"
                ),
            }),
        }

    def clean_attachment(self):
        file = self.cleaned_data.get("attachment")

        if not file:
            return file

        extension = os.path.splitext(file.name)[1].lower()
        content_type = getattr(file, "content_type", "")

        if extension in IMAGE_EXTENSIONS:
            if content_type and content_type not in IMAGE_MIMES:
                raise forms.ValidationError("Invalid image file type.")

            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("Images cannot exceed 10 MB.")

            try:
                from PIL import Image

                image = Image.open(file)
                image.verify()
                file.seek(0)

            except Exception:
                raise forms.ValidationError("The uploaded image is invalid.")

            self.detected_attachment_type = Message.AttachmentType.IMAGE

        elif extension in VIDEO_EXTENSIONS:
            if content_type and content_type not in VIDEO_MIMES:
                raise forms.ValidationError("Invalid video file type.")

            if file.size > 100 * 1024 * 1024:
                raise forms.ValidationError("Videos cannot exceed 100 MB.")

            self.detected_attachment_type = Message.AttachmentType.VIDEO

        else:
            raise forms.ValidationError(
                "Only JPG, PNG, GIF, WEBP, MP4, MOV and WEBM files are allowed."
            )

        return file

    def clean(self):
        cleaned_data = super().clean()

        body = (cleaned_data.get("body") or "").strip()
        attachment = cleaned_data.get("attachment")

        if not body and not attachment:
            raise forms.ValidationError(
                "Write a message or attach an image/video."
            )

        # Important: assign before ModelForm's model validation runs.
        if attachment and hasattr(self, "detected_attachment_type"):
            self.instance.attachment_type = self.detected_attachment_type

        return cleaned_data
