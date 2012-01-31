from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import ugettext

from notification.backends.base import BaseBackend


class EmailBackend(BaseBackend):
    spam_sensitivity = 2
    templates_messages = (
      "short.txt",
      "full.txt",
    )
    template_subject_name = 'notification/email_subject.txt'
    template_body_name = 'notification/email_body.txt'

    def can_send(self, user, notice_type, on_site):
        can_send = super(EmailBackend, self).can_send(user, notice_type, on_site)
        if can_send and user.email:
            return True
        return False

    def send_mail(self, recipient, subject, body):
        return send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient.email])

    def deliver(self, recipient, sender, notice_type, extra_context):
        context = self.get_context()
        context.update({
            "recipient": recipient,
            "sender": sender,
            "notice": ugettext(notice_type.display),
        })
        context.update(extra_context)

        messages = self.get_formatted_messages(notice_type.label, context)

        subject = "".join(render_to_string(self.template_subject_name, {
            "message": messages[self.templates_messages[0]],
        }, context).splitlines())

        body = render_to_string(self.template_body_name, {
            "message": messages[self.templates_messages[1]],
        }, context)

        self.send_mail(recipient, subject, body)
