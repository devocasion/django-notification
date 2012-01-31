from django.core import mail
from django.contrib.auth.models import User
from django.test import TestCase

from notification import models
from django.db.models.signals import post_save


class BaseTest(TestCase):

    class NoticeLables:
        NEW_COMMENT = 'new_comment'

    NOTICE_TYPES = (
        (NoticeLables.NEW_COMMENT, 'New comment', 'You have received new comment notice.'),
    )

    USERS_DETAILS = (
        ('john', 'john@beatles.com', 'john'),
        ('paul', 'paul@beatles.com', 'paul'),
    )

    def setUp(self):
        self.create_notices_types()
        self.create_users()

    def create_notices_types(self):
        for notice_type in self.NOTICE_TYPES:
            models.create_notice_type(*notice_type)

    def create_users(self):
        self.users = []
        for user in self.USERS_DETAILS:
            self.users.append(User.objects.create_user(*user))

    def assert_unseen_notices(self, receiver, on_site_count, emails_count):
        notices = models.Notice.objects.notices_for(receiver, unseen=True)
        self.assertEqual(len(notices), on_site_count)

        to_receiver_mails = 0
        for mail_obj in mail.outbox: #@UndefinedVariable
            if receiver.email in mail_obj.to:
                to_receiver_mails += 1

        self.assertEqual(to_receiver_mails, emails_count) #@UndefinedVariable


class BasicBackendsTest(BaseTest):

    def test_send_notice(self):
        sender = self.users[0]
        receiver = self.users[1]

        models.send([receiver], self.NoticeLables.NEW_COMMENT, extra_context={'from': sender})

        self.assert_unseen_notices(receiver, 1, 1)

    def test_send_email_notice(self):
        sender = self.users[0]
        receiver = self.users[1]

        models.send([receiver], self.NoticeLables.NEW_COMMENT, on_site=False, extra_context={'from': sender})

        self.assert_unseen_notices(receiver, 0, 1)


class ObservedObjectsTest(BaseTest):

    def setUp(self):
        super(ObservedObjectsTest, self).setUp()
        self.observed = User.objects.create_user('observed_obj', 'bserved@obj.com', 'obj')

    def observe(self, observers):
        for observer in observers:
            models.observe(self.observed, observer, self.NoticeLables.NEW_COMMENT)

    def prepare_multiple_observers(self):
        observers = self.users[:2]
        self.observe(observers)
        for observer in observers:
            post_save.send(sender=self.observed.__class__, instance=observer, raw=False, created=False, using='default')
        return observers

    def test_observe(self):
        observers = self.prepare_multiple_observers()

        models.send_observation_notices_for(self.observed)

        for observer in observers:
            self.assert_unseen_notices(observer, 1, 1)

    def test_observe_not_for_sender(self):
        observers = self.prepare_multiple_observers()

        models.send_observation_notices_for(self.observed, sender=observers[1])

        self.assert_unseen_notices(observers[0], 1, 1)
        self.assert_unseen_notices(observers[1], 0, 0)

    def test_is_observing(self):
        observer = self.users[0]
        self.observe([observer])

        self.assertTrue(models.is_observing(self.observed, observer))

    def test_stop_oberving(self):
        observer = self.users[0]
        self.observe([observer])
        self.assertTrue(models.is_observing(self.observed, observer))

        models.stop_observing(self.observed, observer)

        self.assertFalse(models.is_observing(self.observed, observer))
