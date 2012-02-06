from django.utils.translation import ugettext
from django.db.models.loading import get_model
from django.template.context import Context

from notification.backends.base import BaseBackend
from django.contrib.sites.models import Site


class SiteBackend(BaseBackend):
    spam_sensitivity = 1
    templates_messages = (
      "notice.html",
    )

    def can_send(self, user, notice_type, on_site):
        can_send = super(SiteBackend, self).can_send(user, notice_type, on_site)
        if can_send and on_site:
            return True
        return False

    def deliver(self, recipient, sender, notice_type, extra_context):
        context = Context({
            "recipient": recipient,
            "sender": sender,
            "notice": ugettext(notice_type.display),
            "domain": Site.objects.get_current(),
        })
        context.update(extra_context)

        messages = self.get_formatted_messages(notice_type.label, context)

        Notice = get_model('notification', 'Notice')
        Notice.objects.create(recipient=recipient, message=messages[self.templates_messages[0]],
            notice_type=notice_type, on_site=1, sender=sender)
