from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from dashboards.models import BugReport
from prerequisites.models import MailBox


class KanbanMoveTests(TestCase):
    """Drag-and-drop status transitions on the dashboard board."""

    def setUp(self):
        self.user = User.objects.create_user(username="reviewer1", password="x")
        self.client.force_login(self.user)
        MailBox.objects.create(
            mailbox_id=1, email="ops@example.com", password="pw", mailbox_status=1,
        )
        self.report = BugReport.objects.create(
            report_id="AB12CD34EF56",
            report_datetime=timezone.now(),
            hunter_email="hunter@example.com",
            report_reviewer="reviewer",
            report_summary="s",
            report_severitytype="",
            report_status=1,
        )

    def move(self, new_status, report_id="AB12CD34EF56", mailbox_ready=True):
        # check_mailbox_status() reflects the live mail thread (module global),
        # so it is patched explicitly. The notification thread is patched out:
        # these tests only assert the state transition.
        with mock.patch("dashboards.views.geroparser.check_mailbox_status",
                        return_value=mailbox_ready), \
                mock.patch("dashboards.views.threading.Thread") as thread:
            response = self.client.post(f"/dashboard/kanban-move/{report_id}",
                                        {"new_status": new_status})
        return response, thread

    def test_move_updates_status_and_notifies(self):
        response, thread = self.move(3)
        self.assertEqual(response.status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(self.report.report_status, 3)
        thread.assert_called_once()

    def test_rejects_offboard_target(self):
        for bad in (0, 7, 9):
            response, _ = self.move(bad)
            self.assertEqual(response.status_code, 400, bad)
        self.report.refresh_from_db()
        self.assertEqual(self.report.report_status, 1)

    def test_rejects_non_numeric_target(self):
        response, _ = self.move("sideways")
        self.assertEqual(response.status_code, 400)

    def test_rejects_move_from_terminal_status(self):
        self.report.report_status = 7
        self.report.save()
        response, _ = self.move(2)
        self.assertEqual(response.status_code, 400)

    def test_unchanged_move_is_a_noop(self):
        response, thread = self.move(1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "unchanged")
        thread.assert_not_called()

    def test_unknown_report_404(self):
        response, _ = self.move(2, report_id="ZZ99ZZ99ZZ99")
        self.assertEqual(response.status_code, 404)

    def test_requires_configured_mailbox(self):
        response, _ = self.move(2, mailbox_ready=False)
        self.assertEqual(response.status_code, 409)
        self.report.refresh_from_db()
        self.assertEqual(self.report.report_status, 1)

    def test_get_not_allowed(self):
        response = self.client.get("/dashboard/kanban-move/AB12CD34EF56")
        self.assertEqual(response.status_code, 405)

    def test_requires_login(self):
        self.client.logout()
        response = self.client.post("/dashboard/kanban-move/AB12CD34EF56", {"new_status": 2})
        self.assertIn(response.status_code, (302, 403))
