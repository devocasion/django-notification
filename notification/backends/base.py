from django.template.loader import render_to_string
from django.conf import settings
from django.template.context import Context
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse


NOTICES_URL_NAME = getattr(settings, "NOTIFICATION_NOTICES_URL_NAME", "notification_notices")


class BaseBackend(object):
    """
    The base backend.
    """
    def __init__(self, medium_id, spam_sensitivity=None):
        self.medium_id = medium_id
        if spam_sensitivity is not None:
            self.spam_sensitivity = spam_sensitivity

    def can_send(self, user, notice_type, on_site):
        """
        Determines whether this backend is allowed to send a notification to
        the given user and notice_type.
        """
        from notification.models import should_send
        if should_send(user, notice_type, self.medium_id):
            return True
        return False

    def deliver(self, recipient, notice_type, extra_context):
        """
        Deliver a notification to the given recipient.
        """
        raise NotImplemented()

    def get_context(self):
        # TODO: require this to be passed in extra_context
        current_site = Site.objects.get_current()
        notices_url = u"http://%s%s" % (
            unicode(Site.objects.get_current()),
            reverse(NOTICES_URL_NAME),
        )
        context = Context({
            "notices_url": notices_url,
            "current_site": current_site,
        })
        return context

    def get_formatted_messages(self, label, context):
        """
        Returns a dictionary with the format identifier as the key. The values are
        are fully rendered templates with the given context.
        """
        format_templates = {}
        for notice_format in self.templates_messages:
            # conditionally turn off autoescaping for .txt extensions in format
            if notice_format.endswith(".txt"):
                context.autoescape = False
            format_templates[notice_format] = render_to_string((
                "notification/%s/%s" % (label, notice_format),
                "notification/%s" % notice_format), context_instance=context)
        return format_templates
