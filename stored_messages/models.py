from __future__ import unicode_literals

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.contrib.messages.utils import get_level_tags

from .settings import stored_messages_settings

LEVEL_TAGS = get_level_tags()


class MessageManager(models.Manager):
    """
    This custom manager for our Message model allows us to better emulate
    the behavior of builtin Message objects by automatically including the
    applicable level_tag, if available, in the message's tags.
    """
    def create_message(self, *args, **kwargs):
        message = self.create(**kwargs)
        tags = message.tags
        level_tag = message.level_tag

        if tags and level_tag:
            tags = ' '.join([tags, level_tag])
        elif tags:
            tags = tags
        else:
            tags = level_tag

        message.tags = tags
        message.save()
        return message


@python_2_unicode_compatible
class Message(models.Model):
    """
    This model represents a message on the database. Fields are the same as in
    `contrib.messages`
    """
    message = models.TextField()
    level = models.IntegerField()
    tags = models.TextField()
    url = models.URLField(null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)

    # use the extended model  manager
    objects = MessageManager()

    def __str__(self):
        return self.message
    @property
    def level_tag(self):
        return LEVEL_TAGS.get(self.level, '')

@python_2_unicode_compatible
class MessageArchive(models.Model):
    """
    This model holds all the messages users received. Corresponding
    database table will grow indefinitely depending on messages traffic.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    message = models.ForeignKey(Message)

    def __str__(self):
        return "[%s] %s" % (self.user, self.message)


@python_2_unicode_compatible
class Inbox(models.Model):
    """
    Inbox messages are stored in this model until users read them. Once read,
    inbox messages are deleted. Inbox messages have an expire time, after
    that they could be removed by a proper django command. We do not expect
    database table corresponding to this model to grow much.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    message = models.ForeignKey(Message)

    class Meta:
        verbose_name_plural = _('inboxes')

    def expired(self):
        expiration_date = self.message.date + timezone.timedelta(
            days=stored_messages_settings.INBOX_EXPIRE_DAYS)
        return expiration_date <= timezone.now()
    expired.boolean = True  # show a nifty icon in the admin

    def __str__(self):
        return "[%s] %s" % (self.user, self.message)
