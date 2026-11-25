from unittest import mock

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from dashboards.models import BugReport
from geromail.tests import make_report


class SettingsAuthorityTests(TestCase):
    def test_non_superusers_cannot_read_or_mutate_settings(self):
        report = make_report()
        plain = User.objects.create_user('plain')
        staff = User.objects.create_user('staff', is_staff=True)
        reviewer = User.objects.create_user('reviewer')
        reviewer.groups.add(Group.objects.create(name='Reviewer'))
        routes = [('setting', {}), ('resend_email', {}), ('view_logs', {}),
                  ('report_override', {}), ('toggle_hunter_sinkhole', {}),
                  ('hall_of_fame_admin', {}),
                  ('reviewer_handler', {'public_id': 'missing'}),
                  ('notification_handler', {'service': 'slack'})]
        before = list(BugReport.objects.values())
        users_before = list(User.objects.values())
        with mock.patch('dashboards.views.threading.Thread') as thread, mock.patch('dashboards.views.geromailer.write_mail') as mail:
            for user in (None, plain, staff, reviewer):
                client = Client()
                if user:
                    client.force_login(user)
                for name, kwargs in routes:
                    for method in ('get', 'post'):
                        with self.subTest(user=user, route=name, method=method):
                            response = getattr(client, method)(reverse(name, kwargs=kwargs), {'report_id': report.pk})
                            self.assertIn(response.status_code, (302, 403))
            thread.assert_not_called()
            mail.assert_not_called()
        self.assertEqual(list(BugReport.objects.values()), before)
        self.assertEqual(list(User.objects.values('id', 'username', 'is_staff', 'is_superuser')),
                         [{key: row[key] for key in ('id', 'username', 'is_staff', 'is_superuser')} for row in users_before])

    def test_superuser_settings_post_requires_csrf(self):
        admin = User.objects.create_superuser('admin', 'admin@example.com', 'test-only')
        client = Client(enforce_csrf_checks=True)
        client.force_login(admin)
        with mock.patch('dashboards.views.threading.Thread') as thread:
            for route in ('setting', 'resend_email', 'report_override', 'toggle_hunter_sinkhole'):
                self.assertEqual(client.post(reverse(route), {}).status_code, 403)
            thread.assert_not_called()
