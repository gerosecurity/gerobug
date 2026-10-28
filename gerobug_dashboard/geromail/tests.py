import email
import email.message
import io
import os
import re
import shutil
import tempfile
import time
from datetime import timedelta
from unittest import mock

from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dashboards.models import (APPEAL_WINDOW_DAYS, BlacklistRule, BugReport, BugReportAppeal,
                               BugReportNDA, BugReportUpdate, ReportStatus)
from geromail import gerocalculator, gerofilter, geromailer, geronotify, geroparser, mail_templates
from prerequisites.models import MailBox


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

    def setUp(self):
        self.report = make_report()

    def test_classify_update_allowed_within_self_quota(self):
        self.report.report_update_self = gerofilter.SELF_UPDATE_LIMIT - 1
        self.report.save()
        code, _ = gerofilter.classify_action("hunter@example.com", "UPDATE_AB12CD34EF56")
        self.assertEqual(code, 203)

        self.report.report_update_self = gerofilter.SELF_UPDATE_LIMIT
        self.report.save()
        code, _ = gerofilter.classify_action("hunter@example.com", "UPDATE_AB12CD34EF56")
        self.assertEqual(code, 407)

    def test_classify_update_allowed_on_invitation_past_quota(self):
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
            self.assertEqual(self.report.report_permission, 0)

    def test_consume_update_allowance_spends_the_invitation_first(self):
        self.report.report_permission = 4 + 2 + 1
        self.report.save()
        remaining = gerofilter.consume_update_allowance(self.report.report_id)
        self.report.refresh_from_db()
        self.assertEqual(self.report.report_update_self, 0)
        self.assertEqual(remaining, gerofilter.SELF_UPDATE_LIMIT)
        self.assertEqual(self.report.report_permission, 3)

    def test_classify_update_closed_once_bounty_is_in_process(self):
        self.report.report_permission = 4
        for closed_status in (6, 7):
            self.report.report_status = closed_status
            self.report.save()
            code, _ = gerofilter.classify_action("hunter@example.com", "UPDATE_AB12CD34EF56")
            self.assertEqual(code, 408, f"status {closed_status} should refuse updates")

        self.report.report_status = 5
        self.report.save()
        code, _ = gerofilter.classify_action("hunter@example.com", "UPDATE_AB12CD34EF56")
        self.assertEqual(code, 203)

    def test_classify_appeal_stops_at_the_limit(self):
        self.report.report_permission = 2
        self.report.report_appeal = gerofilter.APPEAL_LIMIT - 1
        self.report.save()
        code, _ = gerofilter.classify_action("hunter@example.com", "APPEAL_AB12CD34EF56")
        self.assertEqual(code, 204)

        self.report.report_appeal = gerofilter.APPEAL_LIMIT
        self.report.save()
        code, _ = gerofilter.classify_action("hunter@example.com", "APPEAL_AB12CD34EF56")
        self.assertEqual(code, 409)

    def test_classify_appeal_without_the_window_open_is_unauthorized(self):
        self.report.report_permission = 0
        self.report.save()
        code, _ = gerofilter.classify_action("hunter@example.com", "APPEAL_AB12CD34EF56")
        self.assertEqual(code, 403)

    def test_classify_update_still_checks_ownership(self):
        code, _ = gerofilter.classify_action("intruder@example.com", "UPDATE_AB12CD34EF56")
        self.assertEqual(code, 403)


class AutoAgreeTests(TestCase):

    def setUp(self):
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

        self.assertEqual(self.report.report_status, 6)
        self.assertEqual(self.report.report_permission, 0)
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
        self.report.report_status = 3
        self._calculation_sent(days_ago=APPEAL_WINDOW_DAYS + 10)
        write_mail, _ = self._sweep()
        self.assertEqual(self.report.report_status, 3)
        write_mail.assert_not_called()

    def test_auto_accept_at_is_the_deadline_the_sweep_uses(self):
        self._calculation_sent(days_ago=10)
        self.assertEqual(self.report.auto_accept_at,
                         self.report.report_calc_sent_at + timedelta(days=APPEAL_WINDOW_DAYS))

        self.report.report_permission = 4
        self.assertIsNone(self.report.auto_accept_at)

        self.report.report_permission = 2
        self.report.report_status = 6
        self.assertIsNone(self.report.auto_accept_at)

    def test_round_trip_through_triage_does_not_fire_a_stale_window(self):
        self._calculation_sent(days_ago=APPEAL_WINDOW_DAYS + 10)
        self.report.report_status = 3
        self.report.save()
        self.report.report_status = 5
        self.report.save()
        write_mail, _ = self._sweep()
        self.assertEqual((self.report.report_status, self.report.report_permission), (5, 0))
        self.assertIsNone(self.report.auto_accept_at)
        write_mail.assert_not_called()

    def test_sending_a_calculation_restarts_the_window(self):
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


class BounceMatchTests(TestCase):
    def setUp(self):
        BugReport.objects.create(
            report_id="A3F120261234", report_datetime=timezone.now(),
            hunter_email="Hunter@Example.org", report_reviewer="r",
            report_summary="s", report_severitytype="",
        )

    def test_real_bounce_for_the_reports_hunter_matches(self):
        info = geroparser.parse_bounce(email.message_from_string(POSTFIX_DSN))
        self.assertTrue(geroparser.bounce_matches_report(info))

    def test_forged_recipient_does_not_match(self):
        self.assertFalse(geroparser.bounce_matches_report(
            {"report_id": "A3F120261234", "failed_to": "victim@example.com"}))

    def test_unknown_report_does_not_match(self):
        self.assertFalse(geroparser.bounce_matches_report(
            {"report_id": "unknown", "failed_to": "hunter@example.org"}))


LATIN1_SUBMIT = (
    "From: Jose <me@example.com>\r\n"
    "Subject: SUBMIT_Latin1 finding\r\n"
    "Date: Mon, 12 May 2025 10:00:00 +0200\r\n"
    "Content-Type: text/plain; charset=iso-8859-1\r\n"
    "\r\n"
    "TYPE=Caf\xe9 Injection\r\n"
    "ENDPOINT=https://example.com/caf\xe9\r\n"
    "SUMMARY=A caf\xe9 in the query string breaks the parser badly.\r\n"
).encode("latin-1")


class MessageDecodeTests(SimpleTestCase):

    def test_latin1_body_parses(self):
        msg = geroparser.parse_raw_message(LATIN1_SUBMIT)
        body = geroparser.rm_html_tags(geroparser.extract_email_body(msg))
        self.assertIn("Caf\xe9 Injection", body)
        self.assertIn("SUMMARY=", body)

    def test_missing_date_falls_back_to_now(self):
        msg = email.message_from_string("Subject: SUBMIT_x\n\nbody")
        before = int(time.time())
        ts = geroparser.message_timestamp(msg)
        self.assertGreaterEqual(ts, before)
        self.assertLessEqual(ts, int(time.time()) + 1)

    def test_garbage_date_falls_back(self):
        msg = email.message_from_string("Date: not a date at all\nSubject: x\n\nbody")
        before = int(time.time())
        ts = geroparser.message_timestamp(msg)
        self.assertGreaterEqual(ts, before)

    def test_valid_date_is_used(self):
        msg = geroparser.parse_raw_message(LATIN1_SUBMIT)
        self.assertEqual(geroparser.message_timestamp(msg), 1747036800)


def make_pdf(pad=0):
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >>",
    ]
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    if pad:
        out.write(b"%" + b"A" * pad + b"\n")
    offsets = []
    for number, body in enumerate(objs, start=1):
        offsets.append(out.tell())
        out.write(b"%d 0 obj\n" % number)
        out.write(body)
        out.write(b"\nendobj\n")
    xref = out.tell()
    out.write(b"xref\n0 %d\n" % (len(objs) + 1))
    out.write(b"0000000000 65535 f \n")
    for offset in offsets:
        out.write(b"%010d 00000 n \n" % offset)
    out.write(b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
              % (len(objs) + 1, xref))
    return out.getvalue()


MINIMAL_PDF = make_pdf()


def attach_pdf(msg, data, name="report.pdf", content_type="application/pdf"):
    maintype, subtype = content_type.split("/", 1)
    part = MIMEBase(maintype, subtype)
    part.set_payload(data)
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment", filename=name)
    msg.attach(part)


def raw_mail(subject, body="", sender="hunter@example.com", pdf=None,
             pdf_name="report.pdf", pdf_type="application/pdf",
             date="Mon, 12 May 2025 10:00:00 +0200", html=None):
    msg = MIMEMultipart("mixed")
    msg["From"] = "Hunter <" + sender + ">"
    msg["To"] = "bounty@example.com"
    msg["Subject"] = subject
    msg["Date"] = date
    msg["Return-Path"] = "<" + sender + ">"
    msg["Message-ID"] = "<" + str(abs(hash((subject, body, date)))) + "@example.com>"
    if html is None:
        msg.attach(MIMEText(body, "plain"))
    else:
        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(body, "plain"))
        alt.attach(MIMEText(html, "html"))
        msg.attach(alt)
    if pdf is not None:
        attach_pdf(msg, pdf, pdf_name, pdf_type)
    return msg.as_bytes()


SUBMIT_BODY = ("TYPE=Account Takeover (ATO)\n"
               "ENDPOINT=https://api.example.com/v1/batch\n"
               "SUMMARY=The attacker only needs the public clientId and the org id.")

SUBMIT_HTML = ("<html><body><p>TYPE=Account Takeover (ATO)<br>"
               "ENDPOINT=https://api.example.com/v1/batch<br>"
               "SUMMARY=The attacker only needs the public&nbsp;<code>clientId</code>"
               "&nbsp;and the org id.</p></body></html>")


class FakeIMAP:

    def __init__(self, messages):
        self.messages = list(messages)
        self.selected = None
        self.searches = []

    def select(self, folder):
        self.selected = folder
        return ("OK", [str(len(self.messages)).encode()])

    def search(self, charset, criteria):
        self.searches.append(criteria)
        ids = b" ".join(str(i + 1).encode() for i in range(len(self.messages)))
        return ("OK", [ids])

    def fetch(self, num, parts):
        raw = self.messages[int(num) - 1]
        header = str(num).encode() + b" (RFC822 {" + str(len(raw)).encode() + b"}"
        return ("OK", [(header, raw)])

    def noop(self):
        return ("OK", [b""])

    def logout(self):
        return ("BYE", [b""])


class MailFlowTestCase(TestCase):

    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)
        for module in (geroparser, gerofilter):
            if hasattr(module, "MEDIA_ROOT"):
                patcher = mock.patch.object(module, "MEDIA_ROOT", self.media)
                patcher.start()
                self.addCleanup(patcher.stop)
        self.write_mail = mock.patch.object(geromailer, "write_mail").start()
        self.notify = mock.patch.object(geronotify, "notify").start()
        self.mailer_notify = mock.patch.object(geromailer, "notify").start()
        self.addCleanup(mock.patch.stopall)
        for status_id, name in enumerate(
                ["Invalid", "Received", "In Review", "Reproduced", "Fixing",
                 "Bounty Calculation", "Bounty in Process", "Completed"]):
            ReportStatus.objects.get_or_create(status_id=status_id,
                                               defaults={"status_name": name})
        BlacklistRule.objects.get_or_create(rule_id=1)
        MailBox.objects.get_or_create(mailbox_id=1,
                                      defaults={"email": "bounty@example.com"})

    def deliver(self, *raws):
        geroparser.read_mail(FakeIMAP(raws))
        return self.write_mail.call_args_list

    def sent_codes(self):
        return [call[0][0] for call in self.write_mail.call_args_list]

    def last_payload(self):
        return self.write_mail.call_args[0][1]

    def last_note(self):
        return self.write_mail.call_args[0][1][3]

    def pdf_path(self, report_id, file_id):
        return os.path.join(self.media, report_id, file_id + ".pdf")


class SubmitBodyTests(MailFlowTestCase):

    def test_submit_body_uses_plain_part_over_html(self):
        self.deliver(raw_mail("SUBMIT_Critical Authorization Failure",
                              body=SUBMIT_BODY, html=SUBMIT_HTML, pdf=MINIMAL_PDF))
        self.assertEqual(self.sent_codes(), [201])
        report = BugReport.objects.get()
        self.assertEqual(report.report_attack.strip(), "Account Takeover (ATO)")
        self.assertNotIn("<code>", report.report_summary)
        self.assertIn("clientId and", report.report_summary)

    def test_appeal_with_only_attachment_does_not_crash(self):
        report = make_report(report_status=5, report_permission=2)
        msg = MIMEMultipart("mixed")
        msg["From"] = "Hunter <hunter@example.com>"
        msg["Subject"] = "APPEAL_" + report.report_id
        msg["Date"] = "Mon, 12 May 2025 10:00:00 +0200"
        msg["Return-Path"] = "<hunter@example.com>"
        attach_pdf(msg, MINIMAL_PDF)
        self.deliver(msg.as_bytes())
        self.assertEqual(len(self.sent_codes()), 1)


class ClassifyActionRobustnessTests(TestCase):

    def setUp(self):
        self.report = make_report(report_status=5, report_permission=4 | 2)
        BugReportUpdate.objects.create(
            update_id=self.report.report_id + "U1", report_id=self.report.report_id,
            update_datetime=timezone.now(), update_summary="s", update_file=0)
        BugReportAppeal.objects.create(
            appeal_id=self.report.report_id + "A1", report_id=self.report.report_id,
            appeal_datetime=timezone.now(), appeal_summary="s", appeal_file=0)
        BugReportNDA.objects.create(
            nda_id=self.report.report_id + "N1", report_id=self.report.report_id,
            nda_datetime=timezone.now(), nda_summary="s", nda_file=0)

    def test_uan_id_is_rejected_as_invalid_id(self):
        for verb, suffix in (("CHECK", "U1"), ("UPDATE", "U1"), ("APPEAL", "A1"),
                             ("AGREE", "A1"), ("DATA", "N1"), ("NDA", "N1")):
            with self.subTest(verb=verb):
                code, _ = gerofilter.classify_action(
                    "hunter@example.com", verb + "_" + self.report.report_id + suffix)
                self.assertEqual(code, 405)

    def test_valid_report_id_shape_and_existence(self):
        self.assertTrue(gerofilter.valid_report_id(self.report.report_id))
        self.assertFalse(gerofilter.valid_report_id(self.report.report_id + "U1"))
        self.assertFalse(gerofilter.valid_report_id("SHORT"))
        self.assertFalse(gerofilter.valid_report_id("NOTAREPORT12"))
        self.assertFalse(gerofilter.valid_report_id(""))
        self.assertFalse(gerofilter.valid_report_id(None))

    def test_dashboard_validate_id_still_accepts_uan_ids(self):
        self.assertTrue(gerofilter.validate_id(self.report.report_id + "U1"))
        self.assertTrue(gerofilter.validate_id(self.report.report_id + "A1"))

    def test_exception_returns_404(self):
        with mock.patch.object(gerofilter, "valid_report_id", side_effect=RuntimeError("boom")):
            code, payload = gerofilter.classify_action(
                "hunter@example.com", "CHECK_" + self.report.report_id)
        self.assertEqual(code, 404)
        self.assertEqual(payload, " ")

    def test_classify_never_returns_none(self):
        for subject in ("", "Hello team", "CHECK_", "SUBMIT_", "RANDOM NOISE"):
            with self.subTest(subject=subject):
                self.assertIsNotNone(gerofilter.classify_action("hunter@example.com", subject))


class SubmitValidationTests(MailFlowTestCase):

    def test_rejected_submit_creates_no_media_folder(self):
        self.deliver(raw_mail("SUBMIT_x", body=SUBMIT_BODY, pdf=MINIMAL_PDF))
        self.assertEqual(self.sent_codes(), [404])
        self.assertEqual(self.last_note(), gerofilter.REASON_TITLE)
        self.assertFalse(BugReport.objects.exists())
        self.assertEqual(os.listdir(self.media), [])

    def test_submit_without_pdf_is_refused(self):
        self.deliver(raw_mail("SUBMIT_A good long title", body=SUBMIT_BODY))
        self.assertEqual(self.sent_codes(), [404])
        self.assertEqual(self.last_note(), gerofilter.REASON_SUBMIT_NO_PDF)
        self.assertEqual(os.listdir(self.media), [])

    def test_submit_with_a_non_pdf_attachment_says_so(self):
        self.deliver(raw_mail("SUBMIT_A good long title", body=SUBMIT_BODY,
                              pdf=b"this is not a pdf at all", pdf_name="evil.pdf"))
        self.assertEqual(self.sent_codes(), [404])
        self.assertEqual(self.last_note(), gerofilter.REASON_PDF_INVALID)

    def test_submit_with_an_oversize_pdf_states_the_size(self):
        big = make_pdf(pad=gerofilter.MAX_PDF_BYTES)
        self.deliver(raw_mail("SUBMIT_A good long title", body=SUBMIT_BODY, pdf=big))
        self.assertEqual(self.sent_codes(), [404])
        self.assertIn("the limit is 25 MB", self.last_note())
        self.assertIn(" MB;", self.last_note())
        self.assertEqual(os.listdir(self.media), [])

    def test_submit_endpoint_up_to_255_is_accepted(self):
        endpoint = "https://example.com/" + "a" * 200
        body = ("TYPE=XSS\nENDPOINT=" + endpoint
                + "\nSUMMARY=A long but valid endpoint should be accepted now.")
        self.deliver(raw_mail("SUBMIT_A good long title", body=body, pdf=MINIMAL_PDF))
        self.assertEqual(self.sent_codes(), [201])
        self.assertEqual(BugReport.objects.get().report_endpoint, endpoint)

    def test_submit_short_summary_names_summary(self):
        body = "TYPE=XSS\nENDPOINT=https://example.com/a\nSUMMARY=short"
        self.deliver(raw_mail("SUBMIT_A good long title", body=body, pdf=MINIMAL_PDF))
        self.assertEqual(self.last_note(), gerofilter.REASON_SUMMARY)

    def test_accepted_submit_stores_one_pdf_under_the_new_id(self):
        self.deliver(raw_mail("SUBMIT_A good long title", body=SUBMIT_BODY, pdf=MINIMAL_PDF))
        self.assertEqual(self.sent_codes(), [201])
        report = BugReport.objects.get()
        self.assertRegex(report.report_id, r"^[0-9A-F]{12}$")
        self.assertTrue(os.path.isfile(self.pdf_path(report.report_id, report.report_id)))

class SubmissionOrderingTests(MailFlowTestCase):

    def setUp(self):
        super().setUp()
        self.report = make_report(report_status=5, report_permission=2)

    def test_rejected_appeal_leaves_no_file_and_no_counter(self):
        self.deliver(raw_mail("APPEAL_" + self.report.report_id, body="no"))
        self.assertEqual(self.sent_codes(), [404])
        self.assertEqual(self.last_note(), gerofilter.REASON_EMPTY_APPEAL)
        self.report.refresh_from_db()
        self.assertEqual(self.report.report_appeal, 0)
        self.assertEqual(self.report.report_permission, 2)
        self.assertFalse(BugReportAppeal.objects.exists())
        self.assertEqual(os.listdir(self.media), [])

    def test_second_appeal_after_rejection_stores_its_own_pdf(self):
        self.deliver(raw_mail("APPEAL_" + self.report.report_id, body="no"))
        self.report.report_permission = 2
        self.report.save()
        self.deliver(raw_mail("APPEAL_" + self.report.report_id,
                              body="Here is the full reasoning for the appeal.",
                              pdf=MINIMAL_PDF, date="Tue, 13 May 2025 10:00:00 +0200"))
        self.assertEqual(self.sent_codes(), [404, 204])
        appeal = BugReportAppeal.objects.get()
        self.assertEqual(appeal.appeal_id, self.report.report_id + "A1")
        self.assertEqual(appeal.appeal_file, 1)
        with open(self.pdf_path(self.report.report_id, appeal.appeal_id), "rb") as fp:
            self.assertEqual(fp.read(), MINIMAL_PDF)

    def test_appeal_accepts_a_pdf_with_no_body_text(self):
        self.deliver(raw_mail("APPEAL_" + self.report.report_id, body="", pdf=MINIMAL_PDF))
        self.assertEqual(self.sent_codes(), [204])
        self.assertEqual(BugReportAppeal.objects.get().appeal_file, 1)

    def test_appeal_with_an_oversize_pdf_changes_nothing(self):
        self.deliver(raw_mail("APPEAL_" + self.report.report_id, body="",
                              pdf=make_pdf(pad=gerofilter.MAX_PDF_BYTES)))
        self.assertEqual(self.sent_codes(), [404])
        self.assertIn("the limit is 25 MB", self.last_note())
        self.report.refresh_from_db()
        self.assertEqual((self.report.report_appeal, self.report.report_permission), (0, 2))
        self.assertEqual(os.listdir(self.media), [])

    def test_existing_file_is_never_overwritten(self):
        os.makedirs(os.path.join(self.media, self.report.report_id))
        with open(self.pdf_path(self.report.report_id, self.report.report_id + "A1"), "wb") as fp:
            fp.write(b"original")
        self.assertFalse(gerofilter.store_pdf(
            self.report.report_id, self.report.report_id + "A1", MINIMAL_PDF, base=self.media))
        with open(self.pdf_path(self.report.report_id, self.report.report_id + "A1"), "rb") as fp:
            self.assertEqual(fp.read(), b"original")

    def test_store_pdf_blocks_path_escape(self):
        self.assertFalse(gerofilter.store_pdf(
            "..", os.path.join("..", "escape"), MINIMAL_PDF, base=self.media))
        self.assertEqual(os.listdir(self.media), [])

    def test_update_rechecks_permission_under_lock(self):
        report = make_report("CC11DD22EE33", report_status=2,
                             report_update_self=gerofilter.SELF_UPDATE_LIMIT - 1)
        raw = raw_mail("UPDATE_" + report.report_id,
                       body="Here is the extra detail you asked for.")

        real_classify = gerofilter.classify_action

        def classify_then_exhaust(sender, subject):
            result = real_classify(sender, subject)
            BugReport.objects.filter(report_id=report.report_id).update(
                report_update_self=gerofilter.SELF_UPDATE_LIMIT)
            return result

        with mock.patch.object(gerofilter, "classify_action", side_effect=classify_then_exhaust):
            self.deliver(raw)

        self.assertEqual(self.sent_codes(), [407])
        report.refresh_from_db()
        self.assertEqual(report.report_update, 0)
        self.assertFalse(BugReportUpdate.objects.exists())
        self.assertEqual(os.listdir(self.media), [])

    def test_rejected_update_keeps_the_allowance(self):
        report = make_report("CC11DD22EE33", report_status=2)
        self.deliver(raw_mail("UPDATE_" + report.report_id, body="ok"))
        self.assertEqual(self.sent_codes(), [404])
        self.assertEqual(self.last_note(), gerofilter.REASON_EMPTY_UPDATE)
        report.refresh_from_db()
        self.assertEqual((report.report_update, report.report_update_self), (0, 0))

    def test_accepted_update_spends_the_invitation_first(self):
        report = make_report("CC11DD22EE33", report_status=2, report_permission=4)
        self.deliver(raw_mail("UPDATE_" + report.report_id,
                              body="Here is the extra detail you asked for.",
                              pdf=MINIMAL_PDF))
        self.assertEqual(self.sent_codes(), [203])
        report.refresh_from_db()
        self.assertEqual((report.report_update, report.report_update_self,
                          report.report_permission), (1, 0, 0))
        update = BugReportUpdate.objects.get()
        self.assertEqual(update.update_id, report.report_id + "U1")
        self.assertEqual(update.update_file, 1)

    def test_rejected_data_leaves_no_file_and_no_counter(self):
        report = make_report("CC11DD22EE33", report_status=6, report_permission=1)
        self.deliver(raw_mail("DATA_" + report.report_id, body="no"))
        self.assertEqual(self.sent_codes(), [404])
        report.refresh_from_db()
        self.assertEqual((report.report_nda, report.report_permission), (0, 1))
        self.assertEqual(os.listdir(self.media), [])

    def test_data_without_a_pdf_confirms_with_209(self):
        report = make_report("CC11DD22EE33", report_status=6, report_permission=1)
        self.deliver(raw_mail("DATA_" + report.report_id,
                              body="Account holder name and bank details are below."))
        self.assertEqual(self.sent_codes(), [209])
        report.refresh_from_db()
        self.assertEqual((report.report_nda, report.report_permission), (1, 0))
        self.assertEqual(BugReportNDA.objects.get().nda_file, 0)
