from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from .models import Post, Like, Comment, Follow
from .forms import PostForm


class SocialSetupMixin:

    def create_user(self, username):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="Secure-Test-Pass!9284"
        )


class FeedTests(SocialSetupMixin, TestCase):

    def setUp(self):
        self.user = self.create_user("feeduser")
        self.followed_user = self.create_user("followeduser")
        self.other_user = self.create_user("otheruser")

        self.own_post = Post.objects.create(
            author=self.user,
            caption="My own post"
        )

        self.followed_post = Post.objects.create(
            author=self.followed_user,
            caption="Followed user's post"
        )

        self.other_post = Post.objects.create(
            author=self.other_user,
            caption="Unrelated post"
        )

    def test_feed_requires_login(self):
        response = self.client.get(reverse("social:feed"))

        self.assertEqual(response.status_code, 302)

    def test_feed_shows_own_and_followed_posts(self):
        Follow.objects.create(
            follower=self.user,
            following=self.followed_user
        )

        self.client.force_login(self.user)

        response = self.client.get(reverse("social:feed"))

        self.assertEqual(response.status_code, 200)

        post_ids = list(
            response.context["posts"].values_list("id", flat=True)
        )

        self.assertIn(self.own_post.id, post_ids)
        self.assertIn(self.followed_post.id, post_ids)
        self.assertNotIn(self.other_post.id, post_ids)

    def test_feed_does_not_show_unfollowed_users_posts(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("social:feed"))

        post_ids = list(
            response.context["posts"].values_list("id", flat=True)
        )

        self.assertIn(self.own_post.id, post_ids)
        self.assertNotIn(self.other_post.id, post_ids)


class PostTests(SocialSetupMixin, TestCase):

    def setUp(self):
        self.user = self.create_user("postuser")
        self.other_user = self.create_user("otherpostuser")

        self.post = Post.objects.create(
            author=self.user,
            caption="Original post"
        )

    def test_create_post_with_caption(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("social:post_create"),
            {"caption": "A new ConnectSphere post"}
        )

        self.assertRedirects(response, reverse("social:feed"))

        self.assertTrue(
            Post.objects.filter(
                author=self.user,
                caption="A new ConnectSphere post"
            ).exists()
        )

    def test_empty_post_is_rejected(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("social:post_create"),
            {"caption": ""}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), 1)
        self.assertTrue(response.context["form"].non_field_errors())

    def test_post_form_rejects_empty_content(self):
        form = PostForm(data={"caption": "   "})

        self.assertFalse(form.is_valid())

    def test_edit_own_post(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("social:post_edit", args=[self.post.pk]),
            {"caption": "Updated caption"}
        )

        self.assertRedirects(response, reverse("social:feed"))

        self.post.refresh_from_db()
        self.assertEqual(self.post.caption, "Updated caption")

    def test_user_cannot_edit_another_users_post(self):
        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse("social:post_edit", args=[self.post.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_user_cannot_delete_another_users_post(self):
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse("social:post_delete", args=[self.post.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    def test_delete_requires_post(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("social:post_delete", args=[self.post.pk])
        )

        self.assertEqual(response.status_code, 405)


class LikeTests(SocialSetupMixin, TestCase):

    def setUp(self):
        self.user = self.create_user("likeuser")
        self.author = self.create_user("likeauthor")

        self.post = Post.objects.create(
            author=self.author,
            caption="Like this post"
        )

    def test_like_post(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("social:post_like", args=[self.post.pk])
        )

        self.assertRedirects(response, reverse("social:feed"))
        self.assertTrue(
            Like.objects.filter(
                user=self.user,
                post=self.post
            ).exists()
        )

    def test_unlike_post(self):
        Like.objects.create(user=self.user, post=self.post)
        self.client.force_login(self.user)

        self.client.post(
            reverse("social:post_like", args=[self.post.pk])
        )

        self.assertFalse(
            Like.objects.filter(
                user=self.user,
                post=self.post
            ).exists()
        )

    def test_like_requires_post(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("social:post_like", args=[self.post.pk])
        )

        self.assertEqual(response.status_code, 405)


class CommentTests(SocialSetupMixin, TestCase):

    def setUp(self):
        self.user = self.create_user("commentuser")
        self.author = self.create_user("commentauthor")

        self.post = Post.objects.create(
            author=self.author,
            caption="Post for comments"
        )

    def test_add_comment(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("social:post_comment", args=[self.post.pk]),
            {"content": "Great post!"}
        )

        self.assertRedirects(response, reverse("social:feed"))

        self.assertTrue(
            Comment.objects.filter(
                post=self.post,
                author=self.user,
                content="Great post!"
            ).exists()
        )

    def test_empty_comment_is_rejected(self):
        self.client.force_login(self.user)

        self.client.post(
            reverse("social:post_comment", args=[self.post.pk]),
            {"content": "   "}
        )

        self.assertEqual(Comment.objects.count(), 0)

    def test_comment_over_500_characters_is_rejected(self):
        self.client.force_login(self.user)

        self.client.post(
            reverse("social:post_comment", args=[self.post.pk]),
            {"content": "A" * 501}
        )

        self.assertEqual(Comment.objects.count(), 0)


class FollowTests(SocialSetupMixin, TestCase):

    def setUp(self):
        self.user = self.create_user("follower")
        self.target = self.create_user("targetuser")

    def test_follow_user(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("social:toggle_follow", args=[self.target.username])
        )

        self.assertRedirects(
            response,
            reverse("accounts:profile", args=[self.target.username])
        )

        self.assertTrue(
            Follow.objects.filter(
                follower=self.user,
                following=self.target
            ).exists()
        )

    def test_unfollow_user(self):
        Follow.objects.create(
            follower=self.user,
            following=self.target
        )

        self.client.force_login(self.user)

        self.client.post(
            reverse("social:toggle_follow", args=[self.target.username])
        )

        self.assertFalse(
            Follow.objects.filter(
                follower=self.user,
                following=self.target
            ).exists()
        )

    def test_user_cannot_follow_themselves(self):
        self.client.force_login(self.user)

        self.client.post(
            reverse("social:toggle_follow", args=[self.user.username])
        )

        self.assertFalse(
            Follow.objects.filter(
                follower=self.user,
                following=self.user
            ).exists()
        )

    def test_follow_requires_post(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("social:toggle_follow", args=[self.target.username])
        )

        self.assertEqual(response.status_code, 405)