from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.template.context import Context
from django.utils.translation import ugettext

from notification.backends.base import NOTICES_URL_NAME, BaseBackend
from django.db.models.loading import get_model


class SiteBackend(BaseBackend):
    spam_sensitivity = 1

    def can_send(self, user, notice_type, on_site):
        can_send = super(SiteBackend, self).can_send(user, notice_type, on_site)
        if can_send and on_site:
            return True
        return False

    def deliver(self, recipient, sender, notice_type, extra_context):
        # TODO: require this to be passed in extra_context
        current_site = Site.objects.get_current()
        notices_url = u"http://%s%s" % (
            unicode(Site.objects.get_current()),
            reverse(NOTICES_URL_NAME),
        )

        # update context with user specific translations
        context = Context({
            "recipient": recipient,
            "sender": sender,
            "notice": ugettext(notice_type.display),
            "notices_url": notices_url,
            "current_site": current_site,
        })
        context.update(extra_context)

        messages = self.get_formatted_messages((
            "notice.html",
            "full.html"
        ), notice_type.label, context)

        Notice = get_model('notification', 'Notice')
        Notice.objects.create(recipient=recipient, message=messages['notice.html'],
            notice_type=notice_type, on_site=1, sender=sender)
