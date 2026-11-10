
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import Q, Count, Exists, OuterRef
from django.contrib.auth import get_user_model

from accounts.models import Profile
from .models import Post, Like, Comment, Follow
from .forms import PostForm


@login_required
def feed_view(request):
    user_likes = Like.objects.filter(
        post=OuterRef("pk"),
        user=request.user
    )

    followed_users = Follow.objects.filter(
        follower=request.user
    ).values("following_id")

    posts = (
        Post.objects
        .filter(
            Q(author=request.user) |
            Q(author_id__in=followed_users)
        )
        .select_related("author")
        .prefetch_related("comments__author")
        .annotate(
            likes_count=Count("likes", distinct=True),
            comments_count=Count("comments", distinct=True),
            user_has_liked=Exists(user_likes),
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "social/feed.html",
        {"posts": posts}
    )

@login_required
def user_search_view(request):
    query = request.GET.get("q", "").strip()
    users = []

    if query:
        users = list(
            get_user_model().objects
            .filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )
            .exclude(pk=request.user.pk)
            .order_by("username")[:30]
        )

        profiles = Profile.objects.filter(
            user_id__in=[user.pk for user in users]
        )

        profile_map = {
            profile.user_id: profile
            for profile in profiles
        }

        for user in users:
            user.search_profile = profile_map.get(user.pk)

    return render(
        request,
        "social/user_search.html",
        {
            "query": query,
            "results": users,
        }
    )


@login_required
@require_POST
def post_like_view(request, pk):
    with transaction.atomic():
        post = get_object_or_404(
            Post.objects.select_for_update(),
            pk=pk
        )

        existing_like = Like.objects.filter(
            user=request.user,
            post=post
        ).first()

        if existing_like:
            existing_like.delete()
        else:
            Like.objects.get_or_create(
                user=request.user,
                post=post
            )

    return redirect("social:feed")


@login_required
@require_POST
def post_comment_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    content = request.POST.get("content", "").strip()

    if not content:
        messages.error(request, "Comment cannot be empty.")

    elif len(content) > 500:
        messages.error(
            request,
            "Comment cannot exceed 500 characters."
        )

    else:
        Comment.objects.create(
            post=post,
            author=request.user,
            content=content
        )

        messages.success(request, "Comment added successfully.")

    return redirect("social:feed")


@login_required
def post_create_view(request):
    form = PostForm(
        request.POST or None,
        request.FILES or None
    )

    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()

        messages.success(
            request,
            "Your post has been published successfully."
        )

        return redirect("social:feed")

    return render(
        request,
        "social/post_form.html",
        {
            "form": form,
            "page_title": "Create Post",
            "button_text": "Publish Post",
        }
    )


@login_required
def post_edit_view(request, pk):
    post = get_object_or_404(
        Post,
        pk=pk,
        author=request.user
    )

    form = PostForm(
        request.POST or None,
        request.FILES or None,
        instance=post
    )

    if request.method == "POST" and form.is_valid():
        old_image = post.image
        old_image_name = old_image.name if old_image else None

        updated_post = form.save()
        new_image_name = (
            updated_post.image.name
            if updated_post.image else None
        )

        if old_image_name and old_image_name != new_image_name:
            storage = old_image.storage
            transaction.on_commit(
                lambda: storage.delete(old_image_name)
            )

        messages.success(
            request,
            "Your post has been updated successfully."
        )

        return redirect("social:feed")

    return render(
        request,
        "social/post_form.html",
        {
            "form": form,
            "page_title": "Edit Post",
            "button_text": "Save Changes",
            "post": post,
        }
    )


@login_required
@require_POST
def post_delete_view(request, pk):
    post = get_object_or_404(
        Post,
        pk=pk,
        author=request.user
    )

    image = post.image
    image_name = image.name if image else None
    storage = image.storage if image else None

    post.delete()

    if image_name:
        transaction.on_commit(
            lambda: storage.delete(image_name)
        )

    messages.success(
        request,
        "Your post has been deleted."
    )

    return redirect("social:feed")
@login_required
@require_POST
def toggle_follow_view(request, username):
    target_user = get_object_or_404(
        get_user_model(),
        username=username
    )

    if target_user.pk == request.user.pk:
        messages.error(request, "You cannot follow yourself.")
        return redirect(
            "accounts:profile",
            username=target_user.username
        )

    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        following=target_user
    )

    if created:
        messages.success(
            request,
            f"You are now following @{target_user.username}."
        )
    else:
        follow.delete()
        messages.success(
            request,
            f"You unfollowed @{target_user.username}."
        )

    return redirect(
        "accounts:profile",
        username=target_user.username
    )