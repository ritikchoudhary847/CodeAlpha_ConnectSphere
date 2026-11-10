from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import User
from .models import Conversation, Message
from .forms import MessageForm


class MessagingSetupMixin:

    def create_user(self, username):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="Secure-Test-Pass!9284"
        )

    def create_conversation(self, user_a, user_b):
        user_one, user_two = sorted(
            [user_a, user_b],
            key=lambda user: user.pk
        )

        return Conversation.objects.create(
            user_one=user_one,
            user_two=user_two
        )


class ConversationTests(MessagingSetupMixin, TestCase):

    def setUp(self):
        self.user_one = self.create_user("chatuser1")
        self.user_two = self.create_user("chatuser2")
        self.other_user = self.create_user("outsider")

    def test_start_conversation(self):
        self.client.force_login(self.user_one)

        response = self.client.get(
            reverse(
                "messaging:start",
                args=[self.user_two.username]
            )
        )

        conversation = Conversation.objects.get()

        self.assertRedirects(
            response,
            reverse(
                "messaging:conversation",
                args=[conversation.pk]
            )
        )

        self.assertEqual(conversation.user_one_id, min(
            self.user_one.pk,
            self.user_two.pk
        ))

        self.assertEqual(conversation.user_two_id, max(
            self.user_one.pk,
            self.user_two.pk
        ))

    def test_starting_existing_conversation_does_not_duplicate_it(self):
        conversation = self.create_conversation(
            self.user_one,
            self.user_two
        )

        self.client.force_login(self.user_two)

        self.client.get(
            reverse(
                "messaging:start",
                args=[self.user_one.username]
            )
        )

        self.assertEqual(Conversation.objects.count(), 1)

        self.assertTrue(
            Conversation.objects.filter(pk=conversation.pk).exists()
        )

    def test_user_cannot_start_conversation_with_themselves(self):
        self.client.force_login(self.user_one)

        response = self.client.get(
            reverse(
                "messaging:start",
                args=[self.user_one.username]
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Conversation.objects.count(), 0)

    def test_conversation_requires_login(self):
        conversation = self.create_conversation(
            self.user_one,
            self.user_two
        )

        response = self.client.get(
            reverse(
                "messaging:conversation",
                args=[conversation.pk]
            )
        )

        self.assertEqual(response.status_code, 302)

    def test_non_participant_cannot_access_conversation(self):
        conversation = self.create_conversation(
            self.user_one,
            self.user_two
        )

        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse(
                "messaging:conversation",
                args=[conversation.pk]
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_inbox_shows_only_participant_conversations(self):
        own_conversation = self.create_conversation(
            self.user_one,
            self.user_two
        )

        self.create_conversation(
            self.user_two,
            self.other_user
        )

        self.client.force_login(self.user_one)

        response = self.client.get(reverse("messaging:inbox"))

        self.assertEqual(response.status_code, 200)

        conversation_ids = [
            item["conversation"].pk
            for item in response.context["conversation_data"]
        ]

        self.assertIn(own_conversation.pk, conversation_ids)
        self.assertEqual(len(conversation_ids), 1)


class MessageTests(MessagingSetupMixin, TestCase):

    def setUp(self):
        self.user_one = self.create_user("sender")
        self.user_two = self.create_user("receiver")

        self.conversation = self.create_conversation(
            self.user_one,
            self.user_two
        )

    def test_send_text_message(self):
        self.client.force_login(self.user_one)

        response = self.client.post(
            reverse(
                "messaging:conversation",
                args=[self.conversation.pk]
            ),
            {"body": "Hello from ConnectSphere!"}
        )

        self.assertRedirects(
            response,
            reverse(
                "messaging:conversation",
                args=[self.conversation.pk]
            )
        )

        message = Message.objects.get()

        self.assertEqual(message.sender, self.user_one)
        self.assertEqual(message.conversation, self.conversation)
        self.assertEqual(message.body, "Hello from ConnectSphere!")

    def test_empty_message_is_rejected(self):
        self.client.force_login(self.user_one)

        response = self.client.post(
            reverse(
                "messaging:conversation",
                args=[self.conversation.pk]
            ),
            {"body": ""}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Message.objects.count(), 0)
        self.assertTrue(response.context["form"].non_field_errors())

    def test_received_message_is_marked_as_read(self):
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user_one,
            body="Please read this message."
        )

        self.assertIsNone(message.read_at)

        self.client.force_login(self.user_two)

        response = self.client.get(
            reverse(
                "messaging:conversation",
                args=[self.conversation.pk]
            )
        )

        self.assertEqual(response.status_code, 200)

        message.refresh_from_db()

        self.assertIsNotNone(message.read_at)

    def test_sender_messages_are_not_marked_as_received(self):
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user_one,
            body="My own message."
        )

        self.client.force_login(self.user_one)

        self.client.get(
            reverse(
                "messaging:conversation",
                args=[self.conversation.pk]
            )
        )

        message.refresh_from_db()

        self.assertIsNone(message.read_at)

    def test_message_form_rejects_empty_message(self):
        form = MessageForm(data={"body": ""})

        self.assertFalse(form.is_valid())

    def test_message_form_accepts_valid_video_attachment(self):
        video = SimpleUploadedFile(
            "sample.mp4",
            b"test-video-content",
            content_type="video/mp4"
        )

        form = MessageForm(
            data={"body": ""},
            files={"attachment": video}
        )

        self.assertTrue(form.is_valid(), form.errors)

        self.assertEqual(
            form.instance.attachment_type,
            Message.AttachmentType.VIDEO
        )

    def test_message_form_rejects_unsupported_attachment(self):
        file = SimpleUploadedFile(
            "malware.exe",
            b"invalid-file",
            content_type="application/octet-stream"
        )

        form = MessageForm(
            data={"body": ""},
            files={"attachment": file}
        )

        self.assertFalse(form.is_valid())
        self.assertIn("attachment", form.errors)


class MessageModelValidationTests(MessagingSetupMixin, TestCase):

    def setUp(self):
        self.user_one = self.create_user("validsender")
        self.user_two = self.create_user("validreceiver")
        self.outsider = self.create_user("invalidsender")

        self.conversation = self.create_conversation(
            self.user_one,
            self.user_two
        )

    def test_other_user_cannot_be_message_sender(self):
        message = Message(
            conversation=self.conversation,
            sender=self.outsider,
            body="This should fail."
        )

        with self.assertRaises(Exception):
            message.full_clean()

    def test_conversation_rejects_non_canonical_order(self):
        conversation = Conversation(
            user_one=self.user_two,
            user_two=self.user_one
        )

        with self.assertRaises(Exception):
            conversation.full_clean()