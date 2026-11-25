from unittest import mock

from django.test import TestCase
from django.urls import reverse


class HostHeaderTests(TestCase):
    """Report 4E0A67B01C7D: a forged Host must not reach the password-reset link."""

    def test_forged_host_is_rejected_before_any_mail(self):
        with mock.patch("smtplib.SMTP_SSL") as ssl_smtp, mock.patch("smtplib.SMTP") as smtp:
            response = self.client.post(reverse("password_reset"), {"email": "admin@example.com"},
                                        HTTP_HOST="attacker.example")
        self.assertEqual(response.status_code, 400)
        ssl_smtp.assert_not_called()
        smtp.assert_not_called()

    def test_configured_host_is_accepted(self):
        response = self.client.get(reverse("password_reset"), HTTP_HOST="localhost:6320")
        self.assertEqual(response.status_code, 200)
