from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from dashboards.models import (BlacklistRule, BugReport, CertificateData,
                               Personalization, ReportStatus, StaticRules)
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

    def test_moving_back_revokes_permissions_of_the_later_stage(self):
        self.report.report_status = 5
        self.report.report_permission = 2
        self.report.save()
        response, _ = self.move(2)
        self.assertEqual(response.status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual((self.report.report_status, self.report.report_permission), (2, 0))

    def test_moving_keeps_an_open_amend_request(self):
        self.report.report_status = 2
        self.report.report_permission = 4
        self.report.save()
        self.move(3)
        self.report.refresh_from_db()
        self.assertEqual(self.report.report_permission, 4)


class StatusPermissionTests(TestCase):
    def setUp(self):
        self.report = BugReport.objects.create(
            report_id="AB12CD34EF56", report_datetime=timezone.now(),
            hunter_email="hunter@example.com", report_reviewer="reviewer",
            report_summary="s", report_severitytype="", report_status=5, report_permission=4 | 2,
        )

    def test_unchanged_status_never_touches_permissions(self):
        report = BugReport.objects.get(report_id="AB12CD34EF56")
        report.report_permission = 7
        report.save()
        report.refresh_from_db()
        self.assertEqual(report.report_permission, 7)

    def test_each_stage_keeps_only_its_own_grants(self):
        for status, expected in ((6, 0), (4, 0), (0, 0)):
            report = BugReport.objects.get(report_id="AB12CD34EF56")
            report.report_status, report.report_permission = 5, 7
            report.save()
            report.report_status = status
            report.save()
            report.refresh_from_db()
            self.assertEqual(report.report_permission, 7 & BugReport.STATUS_PERMISSIONS[status], status)
        self.assertEqual(BugReport.STATUS_PERMISSIONS[5], 6)
        self.assertEqual(BugReport.STATUS_PERMISSIONS[6], 1)

    def test_update_fields_save_still_persists_the_revocation(self):
        report = BugReport.objects.get(report_id="AB12CD34EF56")
        report.report_status = 2
        report.save(update_fields=["report_status"])
        report.refresh_from_db()
        self.assertEqual(report.report_permission, 4)

    def test_hunter_agree_advances_without_leaking_the_appeal_bit(self):
        report = BugReport.objects.get(report_id="AB12CD34EF56")
        report.report_permission = 2
        report.save()
        report.report_permission -= 2
        report.save()
        report.report_status += 1
        report.save()
        report.refresh_from_db()
        self.assertEqual((report.report_status, report.report_permission), (6, 0))


class PageRenderTests(TestCase):
    """Every dashboard page must render. The templates share base.html and the
    design system, so a bad block, a missing context key or an unreversible
    url breaks a whole page rather than one widget."""

    STATUS_NAMES = ["Not Valid", "Need To Review", "In Review", "Fixing", "Retest",
                    "Bounty Calculation", "Bounty in Process", "Completed"]

    def setUp(self):
        for i, name in enumerate(self.STATUS_NAMES):
            ReportStatus.objects.get_or_create(status_id=i, defaults={"status_name": name})
        # Singletons that apps.py ready() seeds in a real deployment.
        Personalization.objects.get_or_create(personalize_id=1)
        BlacklistRule.objects.get_or_create(rule_id=1)
        for model in (CertificateData, StaticRules):
            if not model.objects.exists():
                model.objects.create()
        MailBox.objects.create(
            mailbox_id=1, email="ops@example.com", password="pw", mailbox_status=1,
        )
        BugReport.objects.create(
            report_id="AB12CD34EF56",
            report_datetime=timezone.now(),
            hunter_email="hunter@example.com",
            report_reviewer="reviewer",
            report_title="Test finding",
            report_summary="s",
            report_severity=7.5,
            report_severitytype="",
            report_status=1,
        )
        self.user = User.objects.create_superuser(
            username="geromin-test", password="x", email="a@b.c")
        self.client.force_login(self.user)

    def test_pages_render(self):
        for url in ("/dashboard/",
                    "/dashboard/report-detail/AB12CD34EF56",
                    "/dashboard/setting",
                    "/dashboard/report-status/1",
                    "/dashboard/owasp-calculator",
                    "/dashboard/cvss-calculator"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)


class ThemePresetTests(TestCase):
    """The design system puts light text on secondary_1/secondary_2 and white
    text on button_1, so every selectable palette has to clear AA on those
    pairings or the skin ships unreadable."""

    FIELDS = ['main_1', 'main_2', 'secondary_1', 'secondary_2', 'secondary_3', 'button_1']

    @staticmethod
    def _luminance(hex_):
        channels = [int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        channels = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
                    for c in channels]
        return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]

    @classmethod
    def _contrast(cls, a, b):
        la, lb = cls._luminance(a), cls._luminance(b)
        return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)

    @staticmethod
    def _soften(hex_):
        """Approximates --gds-accent-soft: color-mix(accent 55%, white 45%)."""
        channels = [int(hex_[i:i + 2], 16) for i in (1, 3, 5)]
        return '#%02X%02X%02X' % tuple(round(c * 0.55 + 255 * 0.45) for c in channels)

    def test_presets_well_formed(self):
        import re
        hexpat = re.compile(r'^#[0-9A-Fa-f]{6}$')
        self.assertEqual(len(Personalization.THEME_PRESETS), 7)
        for key, preset in Personalization.THEME_PRESETS.items():
            self.assertTrue(preset['name'], key)
            self.assertTrue(preset['description'], key)
            self.assertEqual(set(preset['colors']), set(self.FIELDS), key)
            for field in self.FIELDS:
                self.assertRegex(preset['colors'][field], hexpat)

    def test_gero_dark_matches_brand_defaults(self):
        self.assertEqual(Personalization.THEME_PRESETS['gero-dark']['colors'],
                         Personalization.BRAND_DEFAULTS)

    def test_preset_contrast_constraints(self):
        for key, preset in Personalization.THEME_PRESETS.items():
            colors = preset['colors']
            self.assertGreaterEqual(
                self._contrast(colors['button_1'], '#FFFFFF'), 4.5,
                f"{key}: CTA fails white-text contrast")
            self.assertGreaterEqual(
                self._contrast(self._soften(colors['main_2']), colors['secondary_2']), 4.5,
                f"{key}: softened accent fails on overlay")

    def test_legacy_palette_would_fail_the_same_check(self):
        """Why the backfill exists: the pre-design-system palette put white
        text on a pale pink overlay."""
        legacy = Personalization.LEGACY_DEFAULTS
        self.assertLess(self._contrast(legacy['secondary_2'], '#FFFFFF'), 4.5)


class LegacyPaletteMigrationTests(TestCase):
    """Settings > Personalization colors predate the design system. An install
    still on the old palette has to move, but an operator's own colors must
    never be overwritten."""

    def _theme(self, **colors):
        Personalization.objects.all().delete()
        return Personalization.objects.create(
            personalize_id=1, company_name="GEROBUG", **colors)

    def test_untouched_legacy_install_is_migrated(self):
        self._theme(**Personalization.LEGACY_DEFAULTS)
        self.assertTrue(Personalization.migrate_legacy_palette())
        theme = Personalization.objects.get(personalize_id=1)
        for field, value in Personalization.BRAND_DEFAULTS.items():
            self.assertEqual(getattr(theme, field).upper(), value.upper(), field)

    def test_migration_is_idempotent(self):
        self._theme(**Personalization.LEGACY_DEFAULTS)
        self.assertTrue(Personalization.migrate_legacy_palette())
        self.assertFalse(Personalization.migrate_legacy_palette())

    def test_customized_palette_is_left_alone(self):
        colors = dict(Personalization.LEGACY_DEFAULTS, main_2="#00FF00")
        self._theme(**colors)
        self.assertFalse(Personalization.migrate_legacy_palette())
        theme = Personalization.objects.get(personalize_id=1)
        self.assertEqual(theme.main_2.upper(), "#00FF00")
        self.assertEqual(theme.secondary_2.upper(),
                         Personalization.LEGACY_DEFAULTS["secondary_2"].upper())

    def test_no_theme_row_is_safe(self):
        Personalization.objects.all().delete()
        self.assertFalse(Personalization.migrate_legacy_palette())


class ReportDetailLifecycleTests(PageRenderTests):
    """Auto-accept deadline and the full hunter-submission lists on the report
    detail page. Reuses PageRenderTests' seeded statuses and report."""

    URL = "/dashboard/report-detail/AB12CD34EF56"

    def setUp(self):
        super().setUp()
        self.report = BugReport.objects.get(report_id="AB12CD34EF56")

    def test_pages_render(self):
        pass  # covered by PageRenderTests itself

    # ---- auto-accept deadline ----

    def _await_auto_accept(self, days_ago):
        from datetime import timedelta
        self.report.report_status = 5
        self.report.report_permission = 2   # appeal still open
        self.report.report_calc_sent_at = timezone.now() - timedelta(days=days_ago)
        self.report.save()

    def test_detail_page_shows_the_auto_accept_deadline(self):
        from django.template.defaultfilters import date as date_filter
        self._await_auto_accept(days_ago=10)
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Auto-accepts in")
        self.assertContains(response, date_filter(self.report.auto_accept_at, "j M Y, H:i"))

    def test_detail_page_hides_the_deadline_once_appealed(self):
        self._await_auto_accept(days_ago=10)
        self.report.report_permission = 0   # appeal arrived, bit consumed
        self.report.save()
        self.assertNotContains(self.client.get(self.URL), "Auto-accepts in")

    def test_detail_page_has_no_deadline_before_a_calculation(self):
        self.assertNotContains(self.client.get(self.URL), "Auto-accepts in")

    def test_kanban_card_shows_the_deadline(self):
        self._await_auto_accept(days_ago=10)
        self.assertContains(self.client.get("/dashboard/"), "auto-accepts in")

    # ---- hunter submissions (all, not just the newest) ----

    def _submit(self, kind, n, days_ago, summary, has_file=0):
        from datetime import timedelta
        from dashboards.models import BugReportAppeal, BugReportNDA, BugReportUpdate
        model, prefix = {'U': (BugReportUpdate, 'update'),
                         'A': (BugReportAppeal, 'appeal'),
                         'N': (BugReportNDA, 'nda')}[kind]
        ident = self.report.report_id + kind + str(n)
        return model.objects.create(**{
            prefix + '_id': ident,
            'report_id': self.report.report_id,
            prefix + '_datetime': timezone.now() - timedelta(days=days_ago),
            prefix + '_summary': summary,
            prefix + '_file': has_file,
        })

    def test_every_submission_is_listed_newest_first(self):
        from dashboards.views import build_hunter_submissions
        self._submit('U', 1, days_ago=9, summary="first update")
        self._submit('U', 2, days_ago=5, summary="second update")
        self._submit('U', 3, days_ago=1, summary="third update")
        self._submit('A', 1, days_ago=3, summary="appealing the valuation")
        self._submit('N', 1, days_ago=2, summary="bank details")

        subs = build_hunter_submissions(self.report)
        self.assertEqual([r['tag'] for r in subs['updates']], ['U3', 'U2', 'U1'])
        self.assertEqual([r['tag'] for r in subs['appeals']], ['A1'])
        self.assertEqual([r['tag'] for r in subs['data']], ['N1'])

        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 200)
        for summary in ("first update", "second update", "third update",
                        "appealing the valuation", "bank details"):
            self.assertContains(response, summary)
        for tag in ("U1", "U2", "U3"):
            self.assertContains(response, f"update-detail/{self.report.report_id}{tag}")

    def test_download_link_only_when_the_pdf_is_really_there(self):
        import os
        from dashboards.views import build_hunter_submissions
        from gerobug.settings import MEDIA_ROOT
        self._submit('U', 1, days_ago=1, summary="claims a file", has_file=1)
        self.assertFalse(build_hunter_submissions(self.report)['updates'][0]['has_file'])

        os.makedirs(os.path.join(MEDIA_ROOT, self.report.report_id), exist_ok=True)
        pdf = os.path.join(MEDIA_ROOT, self.report.report_id, self.report.report_id + 'U1.pdf')
        try:
            with open(pdf, 'wb') as fh:
                fh.write(b'%PDF-1.4')
            self.assertTrue(build_hunter_submissions(self.report)['updates'][0]['has_file'])
            self.assertContains(self.client.get(self.URL), "Download PDF")
        finally:
            os.remove(pdf)

    def test_cards_are_omitted_when_nothing_was_submitted(self):
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "<h6>Updates")
        self.assertNotContains(response, "<h6>Appeals")


class TroubleshootTests(TestCase):
    """Settings > Troubleshooting: resend, sinkhole, override, server logs."""

    def setUp(self):
        from django.urls import reverse
        self.reverse = reverse
        for i, name in enumerate(PageRenderTests.STATUS_NAMES):
            ReportStatus.objects.get_or_create(status_id=i, defaults={"status_name": name})
        MailBox.objects.create(mailbox_id=1, email="ops@example.com", password="pw", mailbox_status=1)
        self.report = BugReport.objects.create(
            report_id="AB12CD34EF56", report_datetime=timezone.now(),
            hunter_email="hunter@example.com", report_reviewer="reviewer",
            report_title="Test finding", report_summary="s", report_severity=7.5,
            report_severitytype="", report_status=5, report_permission=2,
        )
        # Singletons apps.py ready() seeds in a real deployment. Explicit pk=1:
        # the views fetch them by id, and Postgres sequences are not reset
        # between test cases.
        Personalization.objects.get_or_create(personalize_id=1)
        BlacklistRule.objects.get_or_create(rule_id=1)
        CertificateData.objects.get_or_create(pk=1)
        StaticRules.objects.get_or_create(pk=1)
        self.admin = User.objects.create_superuser(username="admin1", password="x", email="a@b.c")
        self.client.force_login(self.admin)

    def resend(self):
        """POST the resend form with the SMTP hand-off captured; return the
        (code, payload) write_mail would have been called with."""
        # The resend thread runs inline so the call can be inspected. Its
        # connection.close() would close the test's own Postgres connection,
        # so it is neutralised for the duration.
        with mock.patch("dashboards.views.geroparser.check_mailbox_status", return_value=True), \
                mock.patch("dashboards.views.geromailer.write_mail") as write_mail, \
                mock.patch("dashboards.views.geromailer.notify") as notify, \
                mock.patch("django.db.connection.close"), \
                mock.patch("dashboards.views.threading.Thread",
                           side_effect=lambda target, args=(), **kw: mock.Mock(
                               start=lambda: target(*args))):
            self.client.post(self.reverse("resend_email"), {"report_id": self.report.report_id})
        notify.assert_not_called()   # a resend never fabricates a notification
        if not write_mail.called:
            return None, None
        return write_mail.call_args[0][0], write_mail.call_args[0][1]

    # ---- resend ----

    def test_company_action_records_what_resend_replays(self):
        from geromail import geromailer, geroparser
        with mock.patch.object(geromailer, "write_mail"):
            geroparser.company_action(self.report.report_id, "7.5 HIGH", 702)
        code, payload = self.resend()
        self.assertEqual((code, payload[3]), (702, "7.5 HIGH"))

    def test_nothing_recorded_sends_nothing(self):
        self.assertEqual(self.resend(), (None, None))

    def test_resent_calculation_restarts_the_appeal_window(self):
        """A calculation is resent because the hunter never got it, so the
        30-day window must count from the resend, not the bounced original."""
        from datetime import timedelta
        from dashboards.models import APPEAL_WINDOW_DAYS
        self.report.report_calc_sent_at = timezone.now() - timedelta(days=25)
        self.report.last_email_code, self.report.last_email_note = 702, "7.5 HIGH"
        self.report.save()

        code, payload = self.resend()
        self.assertEqual((code, payload[3]), (702, "7.5 HIGH"))
        self.report.refresh_from_db()
        self.assertGreater(self.report.auto_accept_at,
                           timezone.now() + timedelta(days=APPEAL_WINDOW_DAYS - 1))
        self.assertEqual(self.report.report_permission, 2)   # no permission side effects
        self.assertEqual(self.report.report_status, 5)

    def test_resend_past_bounty_calculation_leaves_the_clock_alone(self):
        from datetime import timedelta
        stamp = timezone.now() - timedelta(days=40)
        self.report.report_status = 6
        self.report.report_calc_sent_at = stamp
        self.report.last_email_code, self.report.last_email_note = 702, "7.5 HIGH"
        self.report.save()
        self.assertEqual(self.resend()[0], 702)
        self.report.refresh_from_db()
        self.assertEqual(self.report.report_calc_sent_at, stamp)

    def test_resend_of_other_emails_does_not_touch_the_clock(self):
        self.report.last_email_code, self.report.last_email_note = 701, "need a PoC"
        self.report.save()
        self.assertEqual(self.resend()[0], 701)
        self.report.refresh_from_db()
        self.assertIsNone(self.report.report_calc_sent_at)

    def test_invalid_handler_records_its_reason(self):
        with mock.patch("dashboards.views.geroparser.check_mailbox_status", return_value=True), \
                mock.patch("dashboards.views.threading.Thread"):
            self.client.post(self.reverse("invalid_handler", args=[self.report.report_id]),
                             {"invalidreasons": "Out of scope: staging host"})
        self.report.refresh_from_db()
        self.assertEqual((self.report.last_email_code, self.report.last_email_note),
                         (300, "Out of scope: staging host"))

    def test_resend_requires_superuser(self):
        reviewer = User.objects.create_user(username="rev", password="x")
        self.client.force_login(reviewer)
        self.report.last_email_code = 702
        self.report.save()
        self.assertEqual(self.resend(), (None, None))

    # ---- sinkhole ----

    def test_sinkhole_toggle_and_banner(self):
        from dashboards.models import TroubleshootSettings
        self.client.post(self.reverse("toggle_hunter_sinkhole"))
        row = TroubleshootSettings.objects.get(settings_id=1)
        self.assertTrue(row.hunter_email_sinkhole)
        self.assertEqual(row.sinkhole_enabled_by, "admin1")
        self.assertContains(self.client.get("/dashboard/"), "Hunter email sinkhole is ACTIVE")

        self.client.post(self.reverse("toggle_hunter_sinkhole"))
        row.refresh_from_db()
        self.assertFalse(row.hunter_email_sinkhole)
        self.assertNotContains(self.client.get("/dashboard/"), "Hunter email sinkhole is ACTIVE")

    def test_sinkhole_suppresses_smtp_but_reports_success(self):
        from dashboards.models import TroubleshootSettings
        from geromail import geromailer
        TroubleshootSettings.objects.create(settings_id=1, hunter_email_sinkhole=True)
        payload = [self.report.report_id, "Title", 5, "note", 7.5]
        with mock.patch.object(geromailer, "connection"), \
                mock.patch.object(geromailer.smtplib, "SMTP_SSL") as smtp_ssl:
            self.assertTrue(geromailer.write_mail(702, payload, "hunter@example.com"))
            smtp_ssl.assert_not_called()

    # ---- override ----

    def test_override_loads_and_saves(self):
        from dashboards.models import BugHunter
        BugHunter.objects.create(hunter_email="hunter@example.com", hunter_username="old", hunter_scores=0)
        data = self.client.get(self.reverse("report_override"),
                               {"report_id": self.report.report_id}).json()
        self.assertTrue(data["ok"])
        self.assertEqual((data["title"], data["hunter_name"]), ("Test finding", "old"))

        self.client.post(self.reverse("report_override"), {
            "report_id": self.report.report_id, "title": "Fixed title", "status": "3",
            "endpoint": "https://e", "attack": "XSS", "duplicate": "1", "hunter_name": "new"})
        self.report.refresh_from_db()
        self.assertEqual((self.report.report_title, self.report.report_status,
                          self.report.report_duplicate), ("Fixed title", 3, 1))
        self.assertEqual(BugHunter.objects.get(hunter_email="hunter@example.com").hunter_username, "new")

    def test_override_rejects_unknown_status(self):
        self.client.post(self.reverse("report_override"), {
            "report_id": self.report.report_id, "title": "x", "status": "99"})
        self.report.refresh_from_db()
        self.assertEqual(self.report.report_title, "Test finding")

    # ---- logs ----

    def test_view_logs_is_superuser_only(self):
        self.assertIn(self.client.get(self.reverse("view_logs")).status_code, (200,))
        self.client.force_login(User.objects.create_user(username="rev", password="x"))
        self.assertEqual(self.client.get(self.reverse("view_logs")).status_code, 403)

    def test_settings_page_renders_the_troubleshoot_tab(self):
        response = self.client.get("/dashboard/setting")
        self.assertEqual(response.status_code, 200)
        for heading in ("Resend Email", "Override Report Fields", "Hunter Email Sinkhole", "Server Logs"):
            self.assertContains(response, heading)
