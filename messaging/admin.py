
from django.contrib import admin
from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = (
        "sender",
        "body",
        "attachment",
        "attachment_type",
        "created_at",
        "read_at",
    )


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_one",
        "user_two",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "user_one__username",
        "user_two__username",
    )
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sender",
        "conversation",
        "attachment_type",
        "created_at",
        "read_at",
    )
    list_filter = ("attachment_type", "created_at")
    search_fields = ("sender__username", "body")
    readonly_fields = ("created_at", "read_at")
