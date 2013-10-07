from . import BaseTest

from django.contrib.messages.storage import default_storage

from stored_messages.models import Inbox, MessageArchive
from stored_messages import add_message, get_messages, STORED_ERROR, DEBUG, ERROR

import mock


class TestStorage(BaseTest):
    def test_store(self):
        self.request._messages = default_storage(self.request)
        self.request._messages.level = DEBUG
        add_message(self.request, STORED_ERROR, "an SOS to the world")
        add_message(self.request, DEBUG, "this won't be persisted")
        storage = get_messages(self.request)
        self.assertEqual(len(storage), 2)
        self.assertEqual(MessageArchive.objects.filter(user=self.user).count(), 1)

    def test_store_with_middleware(self):
        self.client.login(username='test_user', password='123456')
        self.client.get('/create')
        inbox_msg = Inbox.objects.filter(user=self.user).count()
        self.assertEqual(inbox_msg, 1)
        self.client.get('/consume')
        self.assertEqual(Inbox.objects.filter(user=self.user).count(), 0)
        self.assertEqual(MessageArchive.objects.filter(user=self.user).count(), 1)

    def test_store_keep_unread(self):
        self.client.login(username='test_user', password='123456')
        self.client.get('/create')
        self.client.get('/consume', data={'keep_storage': True})
        self.assertEqual(Inbox.objects.filter(user=self.user).count(), 1)
        self.assertEqual(MessageArchive.objects.filter(user=self.user).count(), 1)

    def test_store_anonymous(self):
        self.request.user = mock.MagicMock(wraps=self.user)
        self.request.user.is_anonymous.return_value = True
        self.request.user.is_authenticated.return_value = False
        self.request._messages = default_storage(self.request)
        add_message(self.request, STORED_ERROR, "an SOS to the world")
        add_message(self.request, ERROR, "this error won't be persisted")
        storage = get_messages(self.request)
        self.assertEqual(len(storage), 2)

    def test_add_empty(self):
        self.request._messages = default_storage(self.request)
        add_message(self.request, DEBUG, '')
        self.assertEqual(len(get_messages(self.request)), 0)

    def test_add_mixed(self):
        self.client.login(username='test_user', password='123456')
        self.client.get('/create_mixed')
        self.client.get('/consume')
        self.assertEqual(Inbox.objects.filter(user=self.user).count(), 0)
