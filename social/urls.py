
from django.urls import path
from . import views

app_name = "social"

urlpatterns = [
    path("", views.feed_view, name="feed"),

    path("search/", views.user_search_view, name="user_search"),

    path("post/create/", views.post_create_view, name="post_create"),

    path("post/<int:pk>/edit/", views.post_edit_view, name="post_edit"),

    path("post/<int:pk>/delete/", views.post_delete_view, name="post_delete"),

    path("post/<int:pk>/like/", views.post_like_view, name="post_like"),

    path("post/<int:pk>/comment/", views.post_comment_view, name="post_comment"),

    path( "follow/<str:username>/",views.toggle_follow_view, name="toggle_follow"),
]
