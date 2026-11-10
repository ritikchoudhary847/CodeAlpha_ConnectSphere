from django.test import TestCase
from django.urls import reverse

from .models import User, Profile
from .forms import RegistrationForm, ProfileEditForm


class AccountRegistrationTests(TestCase):

    def setUp(self):
        self.registration_data = {
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "email": "newuser@example.com",
            "password1": "Secure-Test-Pass!9284",
            "password2": "Secure-Test-Pass!9284",
        }

    def test_registration_form_valid(self):
        form = RegistrationForm(data=self.registration_data)

        self.assertTrue(form.is_valid(), form.errors)

    def test_registration_creates_user_and_profile(self):
        response = self.client.post(
            reverse("accounts:register"),
            self.registration_data
        )

        self.assertRedirects(
            response,
            reverse("accounts:login")
        )

        user = User.objects.get(username="newuser")

        self.assertTrue(user.check_password(
            self.registration_data["password1"]
        ))
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            username="existing",
            email="newuser@example.com",
            password="Another-Secure-Pass!9284"
        )

        form = RegistrationForm(data=self.registration_data)

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_invalid_password_confirmation_is_rejected(self):
        data = self.registration_data.copy()
        data["password2"] = "Different-Password!9284"

        form = RegistrationForm(data=data)

        self.assertFalse(form.is_valid())

    def test_authenticated_user_cannot_register_again(self):
        user = User.objects.create_user(
            username="existing",
            email="existing@example.com",
            password="Secure-Test-Pass!9284"
        )

        self.client.force_login(user)

        response = self.client.get(reverse("accounts:register"))

        self.assertRedirects(response, reverse("social:feed"))


class AccountAuthenticationTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="ritik_test",
            email="ritik@example.com",
            password="Secure-Test-Pass!9284"
        )

    def test_login_with_valid_credentials(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "ritik_test",
                "password": "Secure-Test-Pass!9284",
            }
        )

        self.assertRedirects(response, reverse("social:feed"))
        self.assertTrue(
            response.wsgi_request.user.is_authenticated
        )

    def test_login_with_invalid_password(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "ritik_test",
                "password": "Wrong-Password!9284",
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_requires_post(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:logout"))

        self.assertEqual(response.status_code, 405)

    def test_logout_post(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("accounts:logout"))

        self.assertRedirects(response, reverse("accounts:login"))


class ProfileTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="profileuser",
            email="profile@example.com",
            password="Secure-Test-Pass!9284",
            first_name="Profile",
            last_name="User"
        )

    def test_profile_requires_login(self):
        response = self.client.get(
            reverse("accounts:profile", args=["profileuser"])
        )

        self.assertEqual(response.status_code, 302)

    def test_profile_page_creates_missing_profile(self):
        self.client.force_login(self.user)

        self.assertFalse(
            Profile.objects.filter(user=self.user).exists()
        )

        response = self.client.get(
            reverse("accounts:profile", args=["profileuser"])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Profile.objects.filter(user=self.user).exists()
        )

    def test_edit_profile_updates_user_and_profile(self):
        Profile.objects.create(user=self.user)
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:edit_profile"),
            {
                "first_name": "Updated",
                "last_name": "Name",
                "bio": "Building ConnectSphere.",
                "website": "https://example.com",
            }
        )

        self.assertRedirects(
            response,
            reverse("accounts:profile", args=["profileuser"])
        )

        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()

        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.last_name, "Name")
        self.assertEqual(
            self.user.profile.bio,
            "Building ConnectSphere."
        )

    def test_followers_page_requires_login(self):
        response = self.client.get(
            reverse("accounts:followers", args=["profileuser"])
        )

        self.assertEqual(response.status_code, 302)

    def test_following_page_requires_login(self):
        response = self.client.get(
            reverse("accounts:following", args=["profileuser"])
        )

        self.assertEqual(response.status_code, 302)