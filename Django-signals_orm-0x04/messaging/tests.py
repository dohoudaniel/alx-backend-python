from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Message, MessageHistory

User = get_user_model()

class MessageEditHistoryTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username='alice', password='pass')
        self.bob = User.objects.create_user(username='bob', password='pass')

    def test_editing_message_creates_history_and_updates_metadata(self):
        msg = Message.objects.create(sender=self.alice, receiver=self.bob, content='original')

        # simulate an edit done by alice via view: attach transient _editor and save
        msg.content = 'edited content'
        msg._editor = self.alice  # view would set this before saving
        msg.save()

        # Check message is marked edited
        msg.refresh_from_db()
        self.assertTrue(msg.edited)
        self.assertIsNotNone(msg.last_edited_at)
        self.assertEqual(msg.last_edited_by, self.alice)

        # There should be one history record with old content
        histories = MessageHistory.objects.filter(message=msg)
        self.assertEqual(histories.count(), 1)
        hist = histories.first()
        self.assertEqual(hist.old_content, 'original')
        self.assertEqual(hist.editor, self.alice)

    def test_updating_content_to_same_value_does_not_create_history(self):
        msg = Message.objects.create(sender=self.alice, receiver=self.bob, content='same')
        msg.content = 'same'
        msg._editor = self.alice
        msg.save()

        histories = MessageHistory.objects.filter(message=msg)
        self.assertEqual(histories.count(), 0)

