
from django.db import models
from django.conf import settings
from django.db.models import Q, F
from django.core.exceptions import ValidationError


class Conversation(models.Model):
    user_one = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_as_user_one"
    )

    user_two = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_as_user_two"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user_one", "user_two"],
                name="unique_direct_conversation"
            ),
            models.CheckConstraint(
                condition=~Q(user_one=F("user_two")),
                name="prevent_self_conversation"
            ),
        ]

    def clean(self):
        if self.user_one_id and self.user_two_id:
            if self.user_one_id >= self.user_two_id:
                raise ValidationError(
                    "Conversation participants must be stored in canonical order."
                )

    def other_participant(self, user):
        if user.pk == self.user_one_id:
            return self.user_two
        if user.pk == self.user_two_id:
            return self.user_one
        return None

    def __str__(self):
        return f"{self.user_one} - {self.user_two}"


class Message(models.Model):

    class AttachmentType(models.TextChoices):
        IMAGE = "IMAGE", "Image"
        VIDEO = "VIDEO", "Video"

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )

    body = models.TextField(max_length=5000, blank=True)

    attachment = models.FileField(
        upload_to="messages/%Y/%m/",
        blank=True,
        null=True
    )

    attachment_type = models.CharField(
        max_length=10,
        choices=AttachmentType.choices,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    read_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(
                fields=["conversation", "created_at"],
                name="message_conv_date_idx"
            ),
            models.Index(
                fields=["conversation", "read_at"],
                name="message_read_idx"
            ),
        ]

    def clean(self):
        if self.conversation_id and self.sender_id:
            conversation = self.conversation

            if self.sender_id not in (
                conversation.user_one_id,
                conversation.user_two_id
            ):
                raise ValidationError(
                    "Sender must belong to this conversation."
                )

        if self.attachment and not self.attachment_type:
            raise ValidationError(
                "Attachment type is required."
            )

    def __str__(self):
        return f"Message by {self.sender.username}"
