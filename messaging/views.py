
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Conversation, Message
from .forms import MessageForm


User = get_user_model()


@login_required
def inbox_view(request):

    conversations = (
        Conversation.objects
        .filter(
            Q(user_one=request.user) |
            Q(user_two=request.user)
        )
        .select_related("user_one", "user_two")
        .annotate(
            unread_count=Count(
                "messages",
                filter=Q(
                    messages__read_at__isnull=True
                ) & ~Q(messages__sender=request.user)
            )
        )
    )

    conversation_data = []

    for conversation in conversations:
        other_user = conversation.other_participant(request.user)

        latest_message = conversation.messages.select_related(
            "sender"
        ).order_by("-created_at").first()

        conversation_data.append({
            "conversation": conversation,
            "other_user": other_user,
            "latest_message": latest_message,
            "unread_count": conversation.unread_count,
        })

    return render(
        request,
        "messaging/inbox.html",
        {"conversation_data": conversation_data}
    )


@login_required
def start_conversation_view(request, username):

    other_user = get_object_or_404(
        User,
        username=username
    )

    if other_user.pk == request.user.pk:
        messages.error(request, "You cannot chat with yourself.")
        return redirect(
            "accounts:profile",
            username=username
        )

    user_one, user_two = sorted(
        [request.user, other_user],
        key=lambda user: user.pk
    )

    conversation, created = Conversation.objects.get_or_create(
        user_one=user_one,
        user_two=user_two
    )

    return redirect(
        "messaging:conversation",
        conversation_id=conversation.pk
    )


@login_required
def conversation_view(request, conversation_id):

    conversation = get_object_or_404(
        Conversation.objects.select_related(
            "user_one",
            "user_two"
        ),
        Q(user_one=request.user) |
        Q(user_two=request.user),
        pk=conversation_id
    )

    other_user = conversation.other_participant(request.user)

    if request.method == "POST":

        form = MessageForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user


            message.full_clean()
            message.save()

            conversation.updated_at = timezone.now()
            conversation.save(update_fields=["updated_at"])

            return redirect(
                "messaging:conversation",
                conversation_id=conversation.pk
            )

    else:
        form = MessageForm()

    Message.objects.filter(
        conversation=conversation,
        read_at__isnull=True
    ).exclude(
        sender=request.user
    ).update(
        read_at=timezone.now()
    )

    chat_messages = conversation.messages.select_related(
        "sender"
    ).all()

    return render(
        request,
        "messaging/conversation.html",
        {
            "conversation": conversation,
            "other_user": other_user,
            "chat_messages": chat_messages,
            "form": form,
        }
    )
