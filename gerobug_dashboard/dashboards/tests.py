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
