from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import transaction

from .forms import RegistrationForm, ProfileEditForm
from .models import Profile
from social.models import Post, Follow


User = get_user_model()


def register_view(request):
    if request.user.is_authenticated:
        return redirect("social:feed")

    form = RegistrationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = form.save()
            Profile.objects.create(user=user)

        messages.success(
            request,
            "Your ConnectSphere account has been created successfully."
        )

        return redirect("accounts:login")

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("social:feed")

    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)

        messages.success(
            request,
            f"Welcome back, {user.username}!"
        )

        return redirect("social:feed")

    return render(request, "social/login.html", {"form": form})


@login_required
@require_POST
def logout_view(request):
    logout(request)

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect("accounts:login")


@login_required
def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    profile, _ = Profile.objects.get_or_create(user=profile_user)

    posts = Post.objects.filter(
        author=profile_user
    ).order_by("-created_at")
    is_following = Follow.objects.filter(
       follower=request.user,
       following=profile_user
    ).exists()
    context = {
        "profile_user": profile_user,
        "profile": profile,
        "posts": posts,
        "post_count": posts.count(),
        "follower_count": Follow.objects.filter(
            following=profile_user
        ).count(),
        "following_count": Follow.objects.filter(
            follower=profile_user
        ).count(),
        "is_following": is_following,
    }

    return render(request, "accounts/profile.html", context)


@login_required
def edit_profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    form = ProfileEditForm(
        request.POST or None,
        request.FILES or None,
        instance=profile
    )

    if request.method == "POST" and form.is_valid():
        old_image = profile.profile_picture
        old_image_name = old_image.name if old_image else None

        with transaction.atomic():
            updated_profile = form.save()

            new_image_name = (
                updated_profile.profile_picture.name
                if updated_profile.profile_picture
                else None
            )

            if old_image_name and old_image_name != new_image_name:
                storage = old_image.storage
                transaction.on_commit(
                    lambda: storage.delete(old_image_name)
                )

        messages.success(
            request,
            "Your profile has been updated successfully."
        )

        return redirect(
            "accounts:profile",
            username=request.user.username
        )

    return render(
        request,
        "accounts/edit_profile.html",
        {"form": form, "profile": profile}
    )

@login_required
def followers_view(request, username):
    profile_user = get_object_or_404(User, username=username)

    followers = User.objects.filter(
        following__following=profile_user
    ).select_related("profile").order_by("username")

    return render(
        request,
        "accounts/follow_list.html",
        {
            "profile_user": profile_user,
            "people": followers,
            "list_type": "Followers",
            "list_count": followers.count(),
        }
    )


@login_required
def following_view(request, username):
    profile_user = get_object_or_404(User, username=username)

    following = User.objects.filter(
        followers__follower=profile_user
    ).select_related("profile").order_by("username")

    return render(
        request,
        "accounts/follow_list.html",
        {
            "profile_user": profile_user,
            "people": following,
            "list_type": "Following",
            "list_count": following.count(),
        }
    )
