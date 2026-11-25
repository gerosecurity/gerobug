from unittest import mock

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.urls import reverse

import dashboards.signals
from dashboards.models import BlacklistRule, CertificateData, Personalization, StaticRules
from prerequisites.models import MailBox, Webhook


class SettingsActionFixture(TestCase):
    def setUp(self):
        Personalization.objects.get_or_create(personalize_id=1)
        BlacklistRule.objects.get_or_create(rule_id=1)
        for model in (CertificateData, StaticRules):
            model.objects.get_or_create(pk=1)
        MailBox.objects.create(mailbox_id=1, email="ops@example.com", password="pw", mailbox_status=1)
        self.admin = User.objects.create_superuser("admin-test", "admin@example.com", "x")
        self.reviewer = User.objects.create_user("reviewer-one", "reviewer@example.com", "x")
        self.client.force_login(self.admin)

    def notes(self, response):
        return [str(m) for m in get_messages(response.wsgi_request)]


class ResendResetLinkTests(SettingsActionFixture):
    def url(self, user):
        return reverse("resend_reset", kwargs={"public_id": user.profile.public_id.hex})

    def test_superuser_resends_the_link_to_a_reviewer(self):
        with mock.patch("dashboards.views.geroparser.check_mailbox_status", return_value=True), \
                mock.patch("dashboards.views.send_password_reset_link", return_value=True) as send:
            response = self.client.post(self.url(self.reviewer))
        self.assertRedirects(response, reverse("setting"), fetch_redirect_response=False)
        send.assert_called_once()
        self.assertEqual(send.call_args.args[1], self.reviewer)
        self.assertIn("A new password reset link has been sent to reviewer@example.com.", self.notes(response))

    def test_mailbox_not_ready_sends_nothing(self):
        with mock.patch("dashboards.views.geroparser.check_mailbox_status", return_value=False), \
                mock.patch("dashboards.views.send_password_reset_link") as send:
            response = self.client.post(self.url(self.reviewer))
        send.assert_not_called()
        self.assertIn("Mailbox is not ready. Cannot send the reset link right now.", self.notes(response))

    def test_superuser_accounts_are_refused(self):
        with mock.patch("dashboards.views.geroparser.check_mailbox_status", return_value=True), \
                mock.patch("dashboards.views.send_password_reset_link") as send:
            response = self.client.post(self.url(self.admin))
        send.assert_not_called()
        self.assertIn("User not found or not eligible for a reset link.", self.notes(response))

    def test_malformed_identifier_is_refused(self):
        with mock.patch("dashboards.views.send_password_reset_link") as send:
            response = self.client.post(reverse("resend_reset", kwargs={"public_id": "not-a-uuid"}))
        send.assert_not_called()
        self.assertIn("User not found.", self.notes(response))

    def test_reviewer_without_email_is_refused(self):
        self.reviewer.email = ""
        self.reviewer.save()
        with mock.patch("dashboards.views.geroparser.check_mailbox_status", return_value=True), \
                mock.patch("dashboards.views.send_password_reset_link") as send:
            response = self.client.post(self.url(self.reviewer))
        send.assert_not_called()
        self.assertIn("This user has no email address on file.", self.notes(response))

    def test_failed_send_is_reported(self):
        with mock.patch("dashboards.views.geroparser.check_mailbox_status", return_value=True), \
                mock.patch("dashboards.views.send_password_reset_link", return_value=False):
            response = self.client.post(self.url(self.reviewer))
        self.assertIn("Failed to send the reset link. Please check the mailbox settings and the logs.", self.notes(response))

    def test_get_sends_nothing(self):
        with mock.patch("dashboards.views.send_password_reset_link") as send:
            self.client.get(self.url(self.reviewer))
        send.assert_not_called()

    def test_settings_page_offers_resend_for_reviewers_only(self):
        html = self.client.get(reverse("setting")).content.decode()
        self.assertIn(self.url(self.reviewer), html)
        self.assertNotIn(self.url(self.admin), html)


class WebhookEditTests(SettingsActionFixture):
    def setUp(self):
        super().setUp()
        Webhook.objects.create(webhook_service="SLACK", webhook_handle="https://hooks.example.com/old")

    def post(self, service, data):
        return self.client.post(reverse("webhook_edit", kwargs={"service": service}), data)

    def test_handle_is_updated_in_place(self):
        response = self.post("SLACK", {"webhook_service": "SLACK", "webhook_handle": "https://hooks.example.com/new"})
        self.assertEqual(Webhook.objects.count(), 1)
        self.assertEqual(Webhook.objects.get(webhook_service="SLACK").webhook_handle, "https://hooks.example.com/new")
        self.assertIn("Notification Channel Updated Successfully", self.notes(response))

    def test_service_can_change_when_free(self):
        self.post("SLACK", {"webhook_service": "TELEGRAM", "webhook_handle": "https://api.example.com/bot"})
        self.assertEqual(list(Webhook.objects.values_list("webhook_service", flat=True)), ["TELEGRAM"])

    def test_service_cannot_collide_with_another_channel(self):
        Webhook.objects.create(webhook_service="TELEGRAM", webhook_handle="https://api.example.com/bot")
        response = self.post("SLACK", {"webhook_service": "TELEGRAM", "webhook_handle": "https://hooks.example.com/x"})
        self.assertEqual(Webhook.objects.get(webhook_service="SLACK").webhook_handle, "https://hooks.example.com/old")
        self.assertIn("Another notification channel with this service already exists.", self.notes(response))

    def test_unknown_channel_is_reported(self):
        response = self.post("TELEGRAM", {"webhook_service": "TELEGRAM", "webhook_handle": "https://api.example.com/bot"})
        self.assertFalse(Webhook.objects.filter(webhook_service="TELEGRAM").exists())
        self.assertIn("Notification channel not found.", self.notes(response))

    def test_invalid_url_changes_nothing(self):
        response = self.post("SLACK", {"webhook_service": "SLACK", "webhook_handle": "not a url"})
        self.assertEqual(Webhook.objects.get(webhook_service="SLACK").webhook_handle, "https://hooks.example.com/old")
        self.assertIn("Enter a valid webhook URL.", self.notes(response))

    def test_get_changes_nothing(self):
        self.client.get(reverse("webhook_edit", kwargs={"service": "SLACK"}))
        self.assertEqual(Webhook.objects.get(webhook_service="SLACK").webhook_handle, "https://hooks.example.com/old")

    def test_handle_is_stored_encrypted(self):
        from django.db import connection
        self.post("SLACK", {"webhook_service": "SLACK", "webhook_handle": "https://hooks.example.com/secret"})
        with connection.cursor() as cursor:
            cursor.execute("SELECT webhook_handle FROM prerequisites_webhook")
            raw = cursor.fetchone()[0]
        self.assertNotIn("hooks.example.com/secret", raw)

    def test_settings_page_offers_edit_for_each_channel(self):
        html = self.client.get(reverse("setting")).content.decode()
        self.assertIn(reverse("webhook_edit", kwargs={"service": "SLACK"}), html)
        self.assertIn('id="editNotificationModal-SLACK"', html)


class NewSettingsRoutesAuthorityTests(TestCase):
    def test_non_superusers_cannot_use_the_new_routes(self):
        reviewer = User.objects.create_user("reviewer-two", "r2@example.com", "x")
        Webhook.objects.create(webhook_service="SLACK", webhook_handle="https://hooks.example.com/old")
        plain = User.objects.create_user("plain-two")
        staff = User.objects.create_user("staff-two", is_staff=True)
        with mock.patch("dashboards.views.send_password_reset_link") as send:
            for user in (None, plain, staff, reviewer):
                client = Client()
                if user:
                    client.force_login(user)
                for url, data in ((reverse("resend_reset", kwargs={"public_id": reviewer.profile.public_id.hex}), {}),
                                  (reverse("webhook_edit", kwargs={"service": "SLACK"}),
                                   {"webhook_service": "SLACK", "webhook_handle": "https://evil.example.com/x"})):
                    with self.subTest(user=user, url=url):
                        self.assertIn(client.post(url, data).status_code, (302, 403))
            send.assert_not_called()
        self.assertEqual(Webhook.objects.get(webhook_service="SLACK").webhook_handle, "https://hooks.example.com/old")

    def test_new_routes_require_csrf(self):
        admin = User.objects.create_superuser("admin-two", "a2@example.com", "x")
        reviewer = User.objects.create_user("reviewer-three", "r3@example.com", "x")
        client = Client(enforce_csrf_checks=True)
        client.force_login(admin)
        for url in (reverse("resend_reset", kwargs={"public_id": reviewer.profile.public_id.hex}),
                    reverse("webhook_edit", kwargs={"service": "SLACK"})):
            self.assertEqual(client.post(url, {}).status_code, 403)
