from django.test import TestCase

# Create your tests here.
# from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Message, Notification

User = get_user_model()

class MessageNotificationTests(TestCase):
    def setUp(self):
        self.sender = User.objects.create_user(username='alice', password='pass')
        self.receiver = User.objects.create_user(username='bob', password='pass')

    def test_creating_message_creates_notification_for_receiver(self):
        msg = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='Hello Bob!'
        )

        # There should be one notification for the receiver
        notifications = Notification.objects.filter(user=self.receiver)
        self.assertEqual(notifications.count(), 1)

        n = notifications.first()
        self.assertEqual(n.message, msg)
        self.assertIn('sent you a message', n.verb)
        self.assertFalse(n.is_read)

    def test_updating_message_does_not_create_duplicate_notification(self):
        msg = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='First'
        )

        # update message content - should not create another notification
        msg.content = 'Edited'
        msg.save()

        notifications = Notification.objects.filter(user=self.receiver)
        self.assertEqual(notifications.count(), 1)

