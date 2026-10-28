import email
import email.message
from datetime import timedelta
from unittest import mock

from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from dashboards.models import APPEAL_WINDOW_DAYS, BugReport, ReportStatus
from geromail import gerocalculator, gerofilter, geromailer, geronotify, geroparser, mail_templates


APPLE_MAIL_SUBMIT = """\
From: =?utf-8?Q?Jos=C3=A9_Sachs?= <me@example.com>
Content-Type: multipart/mixed; boundary="Apple-Mail=_31CFE82B"
Mime-Version: 1.0 (Mac OS X Mail 16.0)
Subject: SUBMIT_Critical Authorization Failure

--Apple-Mail=_31CFE82B
Content-Transfer-Encoding: quoted-printable
Content-Type: text/plain; charset=us-ascii

TYPE=3DAccount Takeover (ATO)
ENDPOINT=3Dhttps://api.example.com/v1/batch_reports, =
https://login.example.com
SUMMARY=3DA critical vulnerability chain allowing full platform =
compromise. Full details in the PDF.

--Apple-Mail=_31CFE82B
Content-Disposition: inline; filename=report.pdf
Content-Type: application/pdf; name="report.pdf"
Content-Transfer-Encoding: base64

JVBERi0xLjQK

--Apple-Mail=_31CFE82B
Content-Transfer-Encoding: 7bit
Content-Type: text/plain; charset=us-ascii


--Apple-Mail=_31CFE82B--
"""


APPLE_MAIL_UPDATE_ALTERNATIVE = """\
From: =?utf-8?Q?Jos=C3=A9_Sachs?= <me@example.com>
Content-Type: multipart/alternative; boundary="Apple-Mail=_ALT"
Mime-Version: 1.0 (Mac OS X Mail 16.0)
Subject: UPDATE_C20C5B9B563A

--Apple-Mail=_ALT
Content-Transfer-Encoding: quoted-printable
Content-Type: text/plain; charset=utf-8

The attacker only needs the public clientId and the target auth0_org_id =
to generate the ghost user.

--Apple-Mail=_ALT
Content-Type: multipart/mixed; boundary="Apple-Mail=_MIXED"

--Apple-Mail=_MIXED
Content-Transfer-Encoding: quoted-printable
Content-Type: text/html; charset=us-ascii

<html><body><p>The attacker only needs the public&nbsp;<code>clientId</code>&nbsp;and =
the target&nbsp;<code>auth0_org_id</code>&nbsp;to generate the ghost user.</p></body></html>

--Apple-Mail=_MIXED
Content-Disposition: inline; filename=update.pdf
Content-Type: application/pdf; name="update.pdf"
Content-Transfer-Encoding: base64

JVBERi0xLjQK

--Apple-Mail=_MIXED--

--Apple-Mail=_ALT--
"""


class ExtractEmailBodyTests(SimpleTestCase):
    """Apple Mail appends a blank trailing text/plain part after an inline
    attachment; taking the literal last text part wiped the real body and
    made every valid SUBMIT fail as "Details are too short"."""

    def test_blank_trailing_part_does_not_clobber_body(self):
        msg = email.message_from_string(APPLE_MAIL_SUBMIT)
        body = geroparser.rm_html_tags(geroparser.extract_email_body(msg))
        atk_type, endpoint, summary = gerofilter.parse_body(body)

        self.assertEqual(atk_type.strip(), "Account Takeover (ATO)")
        self.assertIn("api.example.com", endpoint)
        self.assertGreater(len(summary), 10)

    def test_multipart_alternative_prefers_plain_over_html(self):
        """A plain branch alongside a mixed(html+attachment) branch: both
        texts are non-blank, so picking whichever comes last in msg.walk()
        picked html half the time. Tag-stripped html glues words together
        ("clientIdand") because &nbsp; around the tag gets stripped too."""
        msg = email.message_from_string(APPLE_MAIL_UPDATE_ALTERNATIVE)
        body = geroparser.rm_html_tags(geroparser.extract_email_body(msg))

        self.assertIn("clientId and", body)
        self.assertNotIn("clientIdand", body)
        self.assertNotIn("<code>", body)


POSTFIX_DSN = """\
From: MAILER-DAEMON@mail.example.com (Mail Delivery System)
Subject: Undelivered Mail Returned to Sender
Return-Path: <>
MIME-Version: 1.0
Content-Type: multipart/report; report-type=delivery-status;
\tboundary="DSN=_BOUNDARY"

--DSN=_BOUNDARY
Content-Type: text/plain; charset=us-ascii

This is the mail system at host mail.example.com.

--DSN=_BOUNDARY
Content-Type: message/delivery-status

Reporting-MTA: dns; mail.example.com

Final-Recipient: rfc822; hunter@example.org
Action: failed
Status: 5.1.1
Diagnostic-Code: smtp; 550 5.1.1 <hunter@example.org>: Recipient address
\trejected: User unknown in virtual mailbox table

--DSN=_BOUNDARY
Content-Type: text/rfc822-headers

Message-ID: <gerobug.1234@mail.example.com>
Subject: [A3F120261234] Your Report Status Has Been Updated
To: hunter@example.org

--DSN=_BOUNDARY--
"""


class ParseBounceTests(SimpleTestCase):
    """A Diagnostic-Code is normally folded across lines; reading the DSN as
    header blocks keeps the whole SMTP error instead of cutting it at the
    first newline."""

    def test_extracts_recipient_error_and_report_id(self):
        info = geroparser.parse_bounce(email.message_from_string(POSTFIX_DSN))

        self.assertEqual(info["failed_to"], "hunter@example.org")
        self.assertEqual(info["report_id"], "A3F120261234")
        self.assertEqual(info["orig_msg_id"], "<gerobug.1234@mail.example.com>")
        self.assertIn("550 5.1.1", info["error"])
        self.assertIn("User unknown in virtual mailbox table", info["error"])

    def test_non_dsn_message_yields_unknowns(self):
        info = geroparser.parse_bounce(email.message_from_string(APPLE_MAIL_SUBMIT))

        self.assertEqual(info["failed_to"], "unknown")
        self.assertEqual(info["report_id"], "unknown")


class SafeHtmlFormatTests(SimpleTestCase):
    """Hunter-controlled text reaches the HTML mail body, so everything is
    escaped and only a short list of formatting tags is allowed back."""

    def test_escapes_markup(self):
        out = geromailer.safe_html_format("<script>alert(1)</script>")

        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)

    def test_keeps_allowed_tags_and_converts_newlines(self):
        out = geromailer.safe_html_format("one\ntwo <b>bold</b>")

        self.assertIn("<br>", out)
        self.assertIn("<b>bold</b>", out)

    def test_none_becomes_dash(self):
        self.assertEqual(geromailer.safe_html_format(None), "-")


class SeverityLabelTests(SimpleTestCase):
    def test_boundaries(self):
        cases = [
            (0, "None"), (0.1, "Low"), (3.9, "Low"),
            (4.0, "Medium"), (6.9, "Medium"),
            (7.0, "High"), (8.9, "High"),
            (9.0, "Critical"), (10.0, "Critical"),
        ]
        for score, expected in cases:
            self.assertEqual(gerocalculator.get_severity_label(score), expected, score)


def make_report(report_id="AB12CD34EF56", **fields):
    defaults = dict(
        report_id=report_id, report_datetime=timezone.now(),
        hunter_email="hunter@example.com", report_reviewer="reviewer",
        report_title="Test finding", report_endpoint="https://example.com/a",
        report_attack="XSS", report_summary="summary", report_severity=7.5,
        report_severitytype="", report_status=2,
    )
    defaults.update(fields)
    return BugReport.objects.create(**defaults)


class HunterAllowanceTests(TestCase):
    """Update/appeal allowances and the update stage gate (gerofilter)."""

    def setUp(self):
        self.report = make_report()

    def test_classify_update_allowed_within_self_quota(self):
        """A hunter may update on their own initiative SELF_UPDATE_LIMIT times
        with no amend request outstanding; the next one is refused with 407
        ("ask the triager"), not the generic 403 ("not authorized")."""
        self.report.report_update_self = gerofilter.SELF_UPDATE_LIMIT - 1
        self.report.save()
        code, _ = gerofilter.classify_action("hunter@example.com", "UPDATE_AB12CD34EF56")
        self.assertEqual(code, 203)

        self.report.report_update_self = gerofilter.SELF_UPDATE_LIMIT
        self.report.save()
        code, _ = gerofilter.classify_action("hunter@example.com", "UPDATE_AB12CD34EF56")
        self.assertEqual(code, 407)

    def test_classify_update_allowed_on_invitation_past_quota(self):
        """An outstanding amend request (the U bit) outranks an exhausted quota."""
        self.report.report_update_self = gerofilter.SELF_UPDATE_LIMIT + 5
        self.report.report_permission = 4
        self.report.save()
        code, _ = gerofilter.classify_action("hunter@example.com", "UPDATE_AB12CD34EF56")
        self.assertEqual(code, 203)

    def test_consume_update_allowance_spends_quota_when_uninvited(self):
        for spent in range(1, gerofilter.SELF_UPDATE_LIMIT + 1):
            remaining = gerofilter.consume_update_allowance(self.report.report_id)
            self.report.refresh_from_db()
            self.assertEqual(self.report.report_update_self, spent)
            self.assertEqual(remaining, gerofilter.SELF_UPDATE_LIMIT - spent)
            self.assertEqual(self.report.report_permission, 0)  # mask never goes negative

    def test_consume_update_allowance_spends_the_invitation_first(self):
        """An amend request pays for the update, so the allowance is untouched;
        the appeal (2) and NDA (1) bits must survive losing the update bit."""
        self.report.report_permission = 4 + 2 + 1
        self.report.save()
        remaining = gerofilter.consume_update_allowance(self.report.report_id)
        self.report.refresh_from_db()
        self.assertEqual(self.report.report_update_self, 0)
        self.assertEqual(remaining, gerofilter.SELF_UPDATE_LIMIT)
        self.assertEqual(self.report.report_permission, 3)  # appeal + NDA intact

    def test_classify_update_closed_once_bounty_is_in_process(self):
        """The stage outranks the permission bit: a grant issued back at
        "In Review" and never spent must not open the door later."""
        self.report.report_permission = 4
        for closed_status in (6, 7):            # Bounty in Process, Completed
            self.report.report_status = closed_status
            self.report.save()
            code, _ = gerofilter.classify_action("hunter@example.com", "UPDATE_AB12CD34EF56")
            self.assertEqual(code, 408, f"status {closed_status} should refuse updates")

        self.report.report_status = 5           # Bounty Calculation: still open
        self.report.save()
        code, _ = gerofilter.classify_action("hunter@example.com", "UPDATE_AB12CD34EF56")
        self.assertEqual(code, 203)

    def test_classify_appeal_stops_at_the_limit(self):
        self.report.report_permission = 2       # appeal window open
        self.report.report_appeal = gerofilter.APPEAL_LIMIT - 1
        self.report.save()
        code, _ = gerofilter.classify_action("hunter@example.com", "APPEAL_AB12CD34EF56")
        self.assertEqual(code, 204)

        self.report.report_appeal = gerofilter.APPEAL_LIMIT
        self.report.save()
        code, _ = gerofilter.classify_action("hunter@example.com", "APPEAL_AB12CD34EF56")
        self.assertEqual(code, 409)   # "determination is final", not "not authorized"

    def test_classify_appeal_without_the_window_open_is_unauthorized(self):
        """Nothing invited an appeal, so 403 stays correct."""
        self.report.report_permission = 0
        self.report.save()
        code, _ = gerofilter.classify_action("hunter@example.com", "APPEAL_AB12CD34EF56")
        self.assertEqual(code, 403)

    def test_classify_update_still_checks_ownership(self):
        code, _ = gerofilter.classify_action("intruder@example.com", "UPDATE_AB12CD34EF56")
        self.assertEqual(code, 403)


class AutoAgreeTests(TestCase):
    """geroparser.check_auto_agree(): a bounty calculation nobody appealed
    within APPEAL_WINDOW_DAYS is accepted on the hunter's behalf, exactly as
    their own AGREE_ reply would be."""

    def setUp(self):
        # Status 5 = Bounty Calculation, permission 2 = appeal window open.
        self.report = make_report(report_status=5, report_permission=2)

    def _calculation_sent(self, days_ago):
        self.report.report_calc_sent_at = timezone.now() - timedelta(days=days_ago)
        self.report.save()

    def _sweep(self):
        with mock.patch.object(geromailer, "write_mail") as write_mail, \
             mock.patch.object(geronotify, "notify") as notify:
            geroparser.check_auto_agree()
        self.report.refresh_from_db()
        return write_mail, notify

    def test_advances_and_emails_after_the_window(self):
        self._calculation_sent(days_ago=APPEAL_WINDOW_DAYS + 1)
        write_mail, notify = self._sweep()

        self.assertEqual(self.report.report_status, 6)      # Bounty in Process
        self.assertEqual(self.report.report_permission, 0)  # appeal bit consumed
        code, payload, destination = write_mail.call_args[0]
        self.assertEqual(code, 302)
        self.assertEqual(destination, "hunter@example.com")
        self.assertEqual(payload[0], "AB12CD34EF56")
        self.assertEqual(payload[2], 6)
        self.assertEqual(notify.call_args[0][2], "NEW_AGREE")

    def test_leaves_report_alone_inside_the_window(self):
        self._calculation_sent(days_ago=APPEAL_WINDOW_DAYS - 1)
        write_mail, _ = self._sweep()
        self.assertEqual(self.report.report_status, 5)
        self.assertEqual(self.report.report_permission, 2)
        write_mail.assert_not_called()

    def test_an_appeal_stops_the_clock(self):
        """Permission 4 (an older amend request) is >= 2 but holds no appeal
        bit, so a value test rather than a bit test would both move the report
        and corrupt the mask."""
        self.report.report_permission = 4
        self._calculation_sent(days_ago=APPEAL_WINDOW_DAYS + 10)
        write_mail, _ = self._sweep()
        self.assertEqual(self.report.report_status, 5)
        self.assertEqual(self.report.report_permission, 4)
        write_mail.assert_not_called()

    def test_no_calculation_on_record_is_not_a_deadline(self):
        write_mail, _ = self._sweep()
        self.assertEqual(self.report.report_status, 5)
        write_mail.assert_not_called()

    def test_only_sweeps_the_bounty_calculation_stage(self):
        self.report.report_status = 3   # Fixing
        self._calculation_sent(days_ago=APPEAL_WINDOW_DAYS + 10)
        write_mail, _ = self._sweep()
        self.assertEqual(self.report.report_status, 3)
        write_mail.assert_not_called()

    def test_auto_accept_at_is_the_deadline_the_sweep_uses(self):
        self._calculation_sent(days_ago=10)
        self.assertEqual(self.report.auto_accept_at,
                         self.report.report_calc_sent_at + timedelta(days=APPEAL_WINDOW_DAYS))

        self.report.report_permission = 4   # appealed: appeal bit consumed
        self.assertIsNone(self.report.auto_accept_at)

        self.report.report_permission = 2
        self.report.report_status = 6       # already in process
        self.assertIsNone(self.report.auto_accept_at)

    def test_sending_a_calculation_restarts_the_window(self):
        """company_action(702) stamps the clock, so a re-sent calculation after
        an appeal gives the hunter a fresh window."""
        self._calculation_sent(days_ago=APPEAL_WINDOW_DAYS + 10)
        with mock.patch.object(geromailer, "write_mail"):
            geroparser.company_action(self.report.report_id, "recalculated", 702)
        write_mail, _ = self._sweep()
        self.assertEqual(self.report.report_status, 5)
        self.assertLess(timezone.now() - self.report.report_calc_sent_at, timedelta(minutes=1))
        write_mail.assert_not_called()


class MailTemplateTests(SimpleTestCase):
    def test_every_code_has_subject_and_body(self):
        self.assertEqual(set(mail_templates.subjectlist), set(mail_templates.messagelist))
        for code in (302, 407, 408, 409):
            self.assertIn(code, mail_templates.messagelist)

    def test_no_placeholder_the_oss_mailer_does_not_fill(self):
        """Enterprise templates carry ~BOUNTY~; the OSS mailer never substitutes
        it, so a stray copy would reach the hunter literally."""
        for code, body in mail_templates.messagelist.items():
            self.assertNotIn("~BOUNTY~", body, code)


class ParseSenderTests(SimpleTestCase):
    def test_rfc2047_quoted_printable_name_is_decoded(self):
        name, addr = geroparser.parse_sender("=?utf-8?Q?Jos=C3=A9_Sachs?= <me@example.com>")
        self.assertEqual(name, "José Sachs")
        self.assertEqual(addr, "me@example.com")

    def test_rfc2047_base64_name_is_decoded(self):
        name, _ = geroparser.parse_sender("=?UTF-8?B?SnVhbiBQw6lyZXo=?= <juan@example.com>")
        self.assertEqual(name, "Juan Pérez")

    def test_plain_name_is_unchanged(self):
        self.assertEqual(geroparser.parse_sender("Plain Name <p@example.com>"),
                         ("Plain Name", "p@example.com"))

    def test_bare_address_keeps_its_last_character(self):
        self.assertEqual(geroparser.parse_sender("me@example.com"), ("me", "me@example.com"))

    def test_quoted_name_with_comma_is_not_split(self):
        name, addr = geroparser.parse_sender('"Sachs, Jose" <js@example.com>')
        self.assertEqual(name, "Sachs Jose")
        self.assertEqual(addr, "js@example.com")

    def test_unknown_charset_degrades_instead_of_raising(self):
        name, addr = geroparser.parse_sender("=?bogus-charset?Q?Broken?= <b@example.com>")
        self.assertEqual(addr, "b@example.com")
        self.assertTrue(name)

    def test_from_without_an_address_is_tolerated(self):
        self.assertEqual(geroparser.parse_sender("MAILER-DAEMON"), ("", ""))

    def test_missing_header_is_tolerated(self):
        self.assertEqual(geroparser.parse_sender(None), ("", ""))


class SenderAuthTests(SimpleTestCase):
    def _msg(self, **headers):
        msg = email.message.EmailMessage()
        for key, value in headers.items():
            msg[key.replace("_", "-")] = value
        return msg

    def test_failed_spf_and_dkim_is_blocked_even_with_matching_return_path(self):
        msg = self._msg(Return_Path="<victim@example.com>",
                        Authentication_Results="mx.example.net; spf=fail; dkim=none")
        self.assertIn("SPF/DKIM failed", geroparser.sender_auth_failure(msg, "victim@example.com"))

    def test_dkim_pass_with_matching_return_path_is_accepted(self):
        msg = self._msg(Return_Path="<hunter@example.com>",
                        Authentication_Results="mx.example.net; spf=softfail; dkim=pass header.d=example.com")
        self.assertIsNone(geroparser.sender_auth_failure(msg, "hunter@example.com"))

    def test_return_path_mismatch_is_blocked(self):
        msg = self._msg(Return_Path="<attacker@evil.test>")
        self.assertIn("mismatch", geroparser.sender_auth_failure(msg, "victim@example.com"))

    def test_missing_return_path_is_blocked(self):
        self.assertIn("no Return-Path", geroparser.sender_auth_failure(self._msg(), "victim@example.com"))

    def test_return_path_comparison_ignores_case(self):
        msg = self._msg(Return_Path="<Hunter@Example.com>")
        self.assertIsNone(geroparser.sender_auth_failure(msg, "hunter@example.com"))


class CheckDuplicateTests(TestCase):
    def test_flags_the_later_report_and_links_the_original(self):
        original = make_report("AA11BB22CC33", report_endpoint="https://API.example.com/v1/orders/",
                               report_attack="IDOR",
                               report_datetime=timezone.now() - timedelta(days=2))
        later = make_report("DD44EE55FF66", report_endpoint="api.example.com/v1/orders?id=1",
                            report_attack="  idor ")
        gerofilter.check_duplicate(later.report_id)
        later.refresh_from_db()
        original.refresh_from_db()
        self.assertEqual((later.report_duplicate, later.report_duplicate_of), (1, "AA11BB22CC33"))
        self.assertEqual(original.report_duplicate, 0)

    def test_out_of_order_processing_still_flags_the_later_report(self):
        make_report("DD44EE55FF66", report_endpoint="https://example.com/a", report_attack="XSS")
        original = make_report("AA11BB22CC33", report_endpoint="example.com/a/", report_attack="XSS",
                               report_datetime=timezone.now() - timedelta(days=2))
        gerofilter.check_duplicate(original.report_id)
        original.refresh_from_db()
        self.assertEqual(original.report_duplicate, 0)
        later = BugReport.objects.get(report_id="DD44EE55FF66")
        self.assertEqual((later.report_duplicate, later.report_duplicate_of), (1, "AA11BB22CC33"))

    def test_different_attack_is_not_a_duplicate(self):
        make_report("AA11BB22CC33", report_endpoint="example.com/a", report_attack="XSS",
                    report_datetime=timezone.now() - timedelta(days=2))
        later = make_report("DD44EE55FF66", report_endpoint="example.com/a", report_attack="SQLi")
        gerofilter.check_duplicate(later.report_id)
        later.refresh_from_db()
        self.assertEqual((later.report_duplicate, later.report_duplicate_of), (0, ""))

    def test_empty_endpoint_never_matches(self):
        make_report("AA11BB22CC33", report_endpoint="", report_attack="XSS",
                    report_datetime=timezone.now() - timedelta(days=2))
        later = make_report("DD44EE55FF66", report_endpoint="", report_attack="XSS")
        gerofilter.check_duplicate(later.report_id)
        later.refresh_from_db()
        self.assertEqual(later.report_duplicate, 0)
