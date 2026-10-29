import datetime as dt
import email
import html
import email.message
import inspect
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

from dashboards.models import (APPEAL_WINDOW_DAYS, PROCESSED_MAIL_RETENTION_DAYS,
                               BlacklistRule, BugHunter, BugReport, BugReportAppeal,
                               BugReportNDA, BugReportUpdate, ProcessedMail, ReportStatus)
from geromail import (gerocalculator, gerocard, gerofilter, geromailer, geronotify,
                      geroparser, mail_templates)
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

    def login(self, user, password):
        return ("OK", [b"LOGIN completed"])

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


class AgreeFlowTests(MailFlowTestCase):

    def setUp(self):
        super().setUp()
        self.report = make_report(report_status=5, report_permission=2)

    def test_agree_sends_exactly_one_mail(self):
        self.deliver(raw_mail("AGREE_" + self.report.report_id))
        self.assertEqual(self.sent_codes(), [205])
        self.mailer_notify.assert_not_called()
        self.report.refresh_from_db()
        self.assertEqual(self.report.report_status, 6)
        self.assertEqual(self.report.report_permission & 2, 0)
        self.assertEqual(self.last_payload()[2], 6)

    def test_agree_after_status_moved_back_is_refused(self):
        raw = raw_mail("AGREE_" + self.report.report_id)
        real_classify = gerofilter.classify_action

        def classify_then_move(sender, subject):
            result = real_classify(sender, subject)
            BugReport.objects.filter(report_id=self.report.report_id).update(
                report_status=3, report_permission=0)
            return result

        with mock.patch.object(gerofilter, "classify_action", side_effect=classify_then_move):
            self.deliver(raw)

        self.assertEqual(self.sent_codes(), [403])
        self.report.refresh_from_db()
        self.assertEqual(self.report.report_status, 3)

    def test_agree_mail_names_the_new_stage(self):
        self.assertIn("Bounty in Process", mail_templates.message_205)


class NoReportsTests(MailFlowTestCase):

    def test_my_score_without_reports_gets_410(self):
        self.deliver(raw_mail("MY_SCORE"))
        self.assertEqual(self.sent_codes(), [410])

    def test_status_overview_without_reports_gets_410(self):
        self.deliver(raw_mail("STATUS_OVERVIEW"))
        self.assertEqual(self.sent_codes(), [410])

    def test_unknown_command_names_help(self):
        self.deliver(raw_mail("Hello team, quick question"))
        self.assertEqual(self.sent_codes(), [404])
        self.assertEqual(self.last_note(), gerofilter.REASON_UNKNOWN_COMMAND)

    def test_404_template_no_longer_claims_the_report_is_invalid(self):
        self.assertNotIn("marked as <b>Invalid</b>", mail_templates.message_404)
        self.assertIn("could not process", mail_templates.message_404)


class ParseBodyTests(SimpleTestCase):

    def test_parse_body_lowercase_and_colon(self):
        atk, endpoint, summary = gerofilter.parse_body(
            "type: SQL Injection\nendpoint: https://example.com/login\n"
            "summary: The login form concatenates the username into the query.")
        self.assertEqual(atk, "SQL Injection")
        self.assertEqual(endpoint, "https://example.com/login")
        self.assertIn("concatenates", summary)

    def test_summary_mentioning_endpoint_is_kept_whole(self):
        _, endpoint, summary = gerofilter.parse_body(
            "TYPE=XSS\nENDPOINT=https://example.com/a\n"
            "SUMMARY=Reflected XSS.\nThe ENDPOINT is reachable without a session.\n"
            "Payload lands in the page title.")
        self.assertEqual(endpoint, "https://example.com/a")
        self.assertIn("Payload lands in the page title.", summary)

    def test_markdown_bold_labels(self):
        atk, endpoint, summary = gerofilter.parse_body(
            "*TYPE* = IDOR\n**ENDPOINT**: https://example.com/orders/1\n"
            "*SUMMARY* - Any user can read any order by changing the id.")
        self.assertEqual(atk, "IDOR")
        self.assertEqual(endpoint, "https://example.com/orders/1")
        self.assertIn("changing the id", summary)

    def test_dash_separator_and_wrapped_endpoint(self):
        _, endpoint, _ = gerofilter.parse_body(
            "TYPE - ATO\nENDPOINT - https://api.example.com/v1/batch,\n"
            "https://login.example.com\nSUMMARY - Full account takeover chain here.")
        self.assertIn("api.example.com", endpoint)
        self.assertIn("login.example.com", endpoint)

    def test_apple_mail_fixture_still_parses(self):
        msg = email.message_from_string(APPLE_MAIL_SUBMIT)
        body = geroparser.rm_html_tags(geroparser.extract_email_body(msg))
        atk, endpoint, summary = gerofilter.parse_body(body)
        self.assertEqual(atk, "Account Takeover (ATO)")
        self.assertIn("api.example.com", endpoint)
        self.assertGreater(len(summary), 10)

    def test_no_fields_yields_empty_strings(self):
        self.assertEqual(gerofilter.parse_body("just a plain reply, thanks"), ("", "", ""))


class ReportIdTests(TestCase):

    def test_generated_ids_are_12_hex_chars(self):
        for _ in range(20):
            report_id = geroparser.generate_id()
            self.assertRegex(report_id, r"^[0-9A-F]{12}$")

    def test_generated_ids_are_never_number_shaped(self):
        for _ in range(200):
            self.assertIsNone(geroparser._NUMERIC_ID_RE.match(geroparser._mint_id()))

    def test_generate_id_skips_an_existing_row(self):
        taken = geroparser._mint_id()
        make_report(taken)
        free = geroparser._mint_id()
        with mock.patch.object(geroparser, "_mint_id", side_effect=[taken, free]):
            self.assertEqual(geroparser.generate_id(), free)

    def test_generate_id_takes_no_arguments(self):
        with self.assertRaises(TypeError):
            geroparser.generate_id("hunter@example.com", 1)


class ImapSanitiseTests(SimpleTestCase):

    def test_imap_string_sanitised(self):
        self.assertEqual(
            geroparser._sanitize_imap_string('a"b\\c\rd\ne'), "abcde")
        self.assertEqual(geroparser._sanitize_imap_string(""), "")
        self.assertEqual(geroparser._sanitize_imap_string(None), "")


class RecoveryTargetTests(TestCase):

    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)
        patcher = mock.patch.object(geroparser, "MEDIA_ROOT", self.media)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.report = make_report()
        os.makedirs(os.path.join(self.media, self.report.report_id))
        with open(os.path.join(self.media, self.report.report_id,
                               self.report.report_id + ".pdf"), "wb") as fp:
            fp.write(b"report")

    def _rows(self):
        base = timezone.now()
        BugReportUpdate.objects.create(
            update_id=self.report.report_id + "U1", report_id=self.report.report_id,
            update_datetime=base - timedelta(days=5), update_summary="s", update_file=1)
        BugReportUpdate.objects.create(
            update_id=self.report.report_id + "U2", report_id=self.report.report_id,
            update_datetime=base - timedelta(days=4), update_summary="s", update_file=1)
        BugReportUpdate.objects.create(
            update_id=self.report.report_id + "U3", report_id=self.report.report_id,
            update_datetime=base - timedelta(days=3), update_summary="s", update_file=0)
        BugReportAppeal.objects.create(
            appeal_id=self.report.report_id + "A1", report_id=self.report.report_id,
            appeal_datetime=base - timedelta(days=2), appeal_summary="s", appeal_file=1)
        BugReportNDA.objects.create(
            nda_id=self.report.report_id + "N1", report_id=self.report.report_id,
            nda_datetime=base - timedelta(days=1), nda_summary="s", nda_file=1)

    def test_recovery_targets_include_appeals_and_older_updates(self):
        self._rows()
        targets = geroparser.missing_submission_files(self.report)
        self.assertEqual(
            [(file_id, kind) for file_id, kind, _ in targets],
            [(self.report.report_id + "U1", "U"),
             (self.report.report_id + "U2", "U"),
             (self.report.report_id + "A1", "A"),
             (self.report.report_id + "N1", "N")])

    def test_rows_without_a_file_are_not_targets(self):
        BugReportUpdate.objects.create(
            update_id=self.report.report_id + "U1", report_id=self.report.report_id,
            update_datetime=timezone.now(), update_summary="s", update_file=0)
        self.assertEqual(geroparser.missing_submission_files(self.report), [])

    def test_present_files_are_not_targets(self):
        self._rows()
        for file_id in ("U1", "U2", "A1", "N1"):
            with open(os.path.join(self.media, self.report.report_id,
                                   self.report.report_id + file_id + ".pdf"), "wb") as fp:
                fp.write(b"x")
        self.assertEqual(geroparser.missing_submission_files(self.report), [])

    def test_missing_report_pdf_is_a_target(self):
        os.remove(os.path.join(self.media, self.report.report_id,
                               self.report.report_id + ".pdf"))
        self.assertEqual(geroparser.missing_submission_files(self.report),
                         [(self.report.report_id, None, None)])


class RecoverySearchTests(TestCase):

    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)
        for module in (geroparser, gerofilter):
            patcher = mock.patch.object(module, "MEDIA_ROOT", self.media)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.report = make_report(report_title='Quoted "title" with \\ slash')
        MailBox.objects.create(mailbox_id=1, email="bounty@example.com",
                               mailbox_type="2")

    def _recover(self, file_id, kind, when, messages):
        fake = FakeIMAP(messages)
        with mock.patch.object(geroparser.imaplib, "IMAP4_SSL", return_value=fake):
            result = geroparser.recover_loss_file(file_id, kind, when)
        return fake, result

    def test_imap_search_strings_are_sanitised(self):
        fake, _ = self._recover(self.report.report_id, None, None, [])
        self.assertTrue(fake.searches)
        for criteria in fake.searches:
            self.assertNotIn('"title"', criteria)
            self.assertNotIn("\\", criteria)
            self.assertIn("Quoted title with  slash", criteria)

    def test_appeal_recovery_searches_appeal_prefix(self):
        fake, _ = self._recover(self.report.report_id + "A1", "A", None, [])
        self.assertIn("APPEAL_" + self.report.report_id, fake.searches[0])

    def test_data_recovery_tries_data_then_nda(self):
        fake, _ = self._recover(self.report.report_id + "N1", "N", None, [])
        self.assertIn("DATA_" + self.report.report_id, fake.searches[0])
        self.assertIn("NDA_" + self.report.report_id, fake.searches[1])

    def test_update_recovery_searches_update_prefix(self):
        fake, _ = self._recover(self.report.report_id + "U1", "U", None, [])
        self.assertIn("UPDATE_" + self.report.report_id, fake.searches[0])

    def test_closest_dated_message_is_recovered(self):
        wanted = raw_mail("UPDATE_" + self.report.report_id, body="first",
                          pdf=MINIMAL_PDF, date="Mon, 12 May 2025 10:00:00 +0000")
        other = raw_mail("UPDATE_" + self.report.report_id, body="second",
                         pdf=make_pdf(pad=16), date="Mon, 19 May 2025 10:00:00 +0000")
        when = dt.datetime(2025, 5, 12, 11, 0, tzinfo=dt.timezone.utc)
        _, result = self._recover(self.report.report_id + "U1", "U", when, [wanted, other])
        self.assertTrue(result)
        path = os.path.join(self.media, self.report.report_id,
                            self.report.report_id + "U1.pdf")
        with open(path, "rb") as fp:
            self.assertEqual(fp.read(), MINIMAL_PDF)

    def test_without_a_date_the_latest_message_is_used(self):
        first = raw_mail("UPDATE_" + self.report.report_id, body="first",
                         pdf=MINIMAL_PDF, date="Mon, 12 May 2025 10:00:00 +0000")
        latest = raw_mail("UPDATE_" + self.report.report_id, body="second",
                          pdf=make_pdf(pad=16), date="Mon, 19 May 2025 10:00:00 +0000")
        _, result = self._recover(self.report.report_id + "U1", "U", None, [first, latest])
        self.assertTrue(result)
        path = os.path.join(self.media, self.report.report_id,
                            self.report.report_id + "U1.pdf")
        with open(path, "rb") as fp:
            self.assertEqual(fp.read(), make_pdf(pad=16))
class ParseSubjectTests(SimpleTestCase):

    def test_table(self):
        cases = [
            ("UPDATE_AB12CD34EF56", ("UPDATE", "AB12CD34EF56")),
            ("Re: update_ab12cd34ef56", ("UPDATE", "AB12CD34EF56")),
            ("RE: [EXT] Fwd: APPEAL_ AB12 CD34 EF56", ("APPEAL", "AB12CD34EF56")),
            ("Re: UPDATE_AB12CD34EF56 | Action Required: Additional Info",
             ("UPDATE", "AB12CD34EF56")),
            ("DATA_AB12CD34EF56 | Action Required: Bounty Prerequisites",
             ("DATA", "AB12CD34EF56")),
            ("CHECK_AB12CD34EF56 | Status of Report AB12CD34EF56",
             ("CHECK", "AB12CD34EF56")),
            ("submit_SQLi on /login", ("SUBMIT", "SQLi on /login")),
            ("SUBMIT_SQLi on /login", ("SUBMIT", "SQLi on /login")),
            ("status_overview", ("STATUS_OVERVIEW", "")),
            ("Re: STATUS_OVERVIEW", ("STATUS_OVERVIEW", "")),
            ("my_score", ("MY_SCORE", "")),
            ("HELP", ("HELP", "")),
            ("commands", ("COMMANDS", "")),
            ("COMMENT_AB12CD34EF56", ("COMMENT", "AB12CD34EF56")),
            ("WITHDRAW_AB12CD34EF56", ("WITHDRAW", "AB12CD34EF56")),
            ("NDA_AB12CD34EF56", ("NDA", "AB12CD34EF56")),
            ("AGREE: AB12CD34EF56", ("AGREE", "AB12CD34EF56")),
            ("AGREE AB12CD34EF56", ("AGREE", "AB12CD34EF56")),
            ("agree-ab12cd34ef56", ("AGREE", "AB12CD34EF56")),
            ("CHECK_AB12CD34EF56U1", ("CHECK", "AB12CD34EF56U1")),
            ("Hello team", (None, "")),
            ("", (None, "")),
            (None, (None, "")),
            ("Aw: Wg: CHECK_AB12CD34EF56", ("CHECK", "AB12CD34EF56")),
        ]
        for subject, expected in cases:
            with self.subTest(subject=subject):
                self.assertEqual(gerofilter.parse_subject(subject), expected)

    def test_report_id_is_uppercased_but_submit_title_is_not(self):
        self.assertEqual(gerofilter.parse_subject("check_ab12cd34ef56")[1], "AB12CD34EF56")
        self.assertEqual(gerofilter.parse_subject("SUBMIT_Mixed Case Title")[1],
                         "Mixed Case Title")

    def test_unterminated_bracket_is_not_a_prefix(self):
        self.assertEqual(gerofilter.parse_subject("[not closed CHECK_AB12CD34EF56"),
                         (None, ""))


class SubjectRegressionTests(TestCase):

    def setUp(self):
        self.report = make_report(report_status=5, report_permission=4 | 2 | 1)
        for status_id, name in enumerate(
                ["Invalid", "Received", "In Review", "Reproduced", "Fixing",
                 "Bounty Calculation", "Bounty in Process", "Completed"]):
            ReportStatus.objects.get_or_create(status_id=status_id,
                                               defaults={"status_name": name})

    def test_old_subject_formats_still_classify(self):
        rid = self.report.report_id
        cases = [
            ("SUBMIT_A good long title", 201),
            ("CHECK_" + rid, 202),
            ("UPDATE_" + rid, 203),
            ("APPEAL_" + rid, 204),
            ("AGREE_" + rid, 205),
            ("NDA_" + rid, 206),
            ("DATA_" + rid, 206),
            ("STATUS_OVERVIEW", 208),
            ("CHECK_ZZ99ZZ99ZZ99", 405),
            ("Hello team", 404),
        ]
        for subject, expected in cases:
            with self.subTest(subject=subject):
                code, _ = gerofilter.classify_action("hunter@example.com", subject)
                self.assertEqual(code, expected)

    def test_my_score_classifies_for_a_hunter_with_reports(self):
        BugHunter.objects.create(hunter_email="hunter@example.com",
                                 hunter_username="h", hunter_scores=7)
        code, payload = gerofilter.classify_action("hunter@example.com", "MY_SCORE")
        self.assertEqual((code, payload), (207, "7"))

    def test_spaced_id_still_resolves(self):
        code, payload = gerofilter.classify_action(
            "hunter@example.com", "CHECK_ " + " ".join(
                [self.report.report_id[i:i + 4] for i in range(0, 12, 4)]))
        self.assertEqual((code, payload), (202, self.report.report_id))

    def test_help_and_commands_answer_with_the_command_list(self):
        for verb in ("HELP", "COMMANDS", "help"):
            with self.subTest(verb=verb):
                code, payload = gerofilter.classify_action("hunter@example.com", verb)
                self.assertEqual(code, 210)
                self.assertIn("STATUS_OVERVIEW", payload)

    def test_non_owner_check_is_forbidden_not_widened(self):
        code, payload = gerofilter.classify_action(
            "someone.else@example.com", "Re: CHECK_" + self.report.report_id)
        self.assertEqual((code, payload), (403, self.report.report_id))

    def test_reply_to_701_subject_classifies_as_update(self):
        make_report("CC11DD22EE33", report_status=2, report_permission=4)
        subject = mail_templates.subjectlist[701].replace("~ID~", "CC11DD22EE33")
        code, payload = gerofilter.classify_action("hunter@example.com", "Re: " + subject)
        self.assertEqual((code, payload), (203, "CC11DD22EE33"))

    def test_reply_to_703_and_705_subjects_classify_as_data(self):
        make_report("CC11DD22EE33", report_status=6, report_permission=1)
        for code_id in (703, 705):
            with self.subTest(code=code_id):
                subject = mail_templates.subjectlist[code_id].replace("~ID~", "CC11DD22EE33")
                code, payload = gerofilter.classify_action(
                    "hunter@example.com", "Re: " + subject)
                self.assertEqual((code, payload), (206, "CC11DD22EE33"))

    def test_reply_to_202_subject_classifies_as_check(self):
        subject = mail_templates.subjectlist[202].replace("~ID~", self.report.report_id)
        code, payload = gerofilter.classify_action("hunter@example.com", "Re: " + subject)
        self.assertEqual((code, payload), (202, self.report.report_id))


class OperatorSubjectTests(SimpleTestCase):

    def test_operator_subjects_lead_with_the_reply_command(self):
        self.assertEqual(mail_templates.subjectlist[701],
                         "UPDATE_~ID~ | Action Required: Additional Info")
        self.assertEqual(mail_templates.subjectlist[703],
                         "DATA_~ID~ | Action Required: Bounty Prerequisites (NDA)")
        self.assertEqual(mail_templates.subjectlist[705],
                         "DATA_~ID~ | Action Required: Bounty Prerequisites")
        self.assertEqual(mail_templates.subjectlist[202],
                         "CHECK_~ID~ | Status of Report ~ID~")

    def test_bodies_offer_a_plain_reply(self):
        for code in (701, 703, 705):
            with self.subTest(code=code):
                self.assertIn("Reply to this email, or send a new email with the subject",
                              mail_templates.messagelist[code])

    def test_208_points_at_check_and_comment(self):
        body = mail_templates.messagelist[208]
        self.assertNotIn("simply reply to this", body)
        self.assertIn("<b>CHECK_</b>", body)
        self.assertIn("<b>COMMENT_</b>", body)
class ThreadHeaderTests(SimpleTestCase):

    def test_reply_sets_in_reply_to_and_references(self):
        parent, references = geromailer.thread_headers(
            "AB12CD34EF56", "example.com", "<inbound@mail.example>")
        self.assertEqual(parent, "<inbound@mail.example>")
        self.assertEqual(
            references,
            "<gerobug-report-AB12CD34EF56@example.com> <inbound@mail.example>")

    def test_report_token_is_present_without_a_parent(self):
        parent, references = geromailer.thread_headers(
            "AB12CD34EF56", "example.com", None)
        self.assertEqual(parent, "")
        self.assertEqual(references, "<gerobug-report-AB12CD34EF56@example.com>")

    def test_no_report_id_means_no_token(self):
        for report_id in ("", " ", None, "AB12CD34EF56U1", "SHORT"):
            with self.subTest(report_id=report_id):
                self.assertEqual(
                    geromailer.report_thread_token(report_id, "example.com"), "")

    def test_header_newlines_stripped(self):
        parent, references = geromailer.thread_headers(
            "AB12CD34EF56", "example.com",
            "<a@b>\r\nBcc: victim@example.com")
        self.assertNotIn("\r", parent + references)
        self.assertNotIn("\n", parent + references)
        self.assertEqual(parent, "<a@b>Bcc: victim@example.com")

    def test_clean_header_strips_cr_and_lf(self):
        self.assertEqual(
            geromailer.clean_header("Subject line\r\nX-Injected: yes"),
            "Subject lineX-Injected: yes")
        self.assertEqual(geromailer.clean_header(None), "")


class ThreadedReplyTests(TestCase):

    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)
        for status_id, name in enumerate(
                ["Invalid", "Received", "In Review", "Reproduced", "Fixing",
                 "Bounty Calculation", "Bounty in Process", "Completed"]):
            ReportStatus.objects.get_or_create(status_id=status_id,
                                               defaults={"status_name": name})
        MailBox.objects.get_or_create(
            mailbox_id=1, defaults={"email": "bounty@example.com",
                                    "password": "secret"})
        self.report = make_report()
        closer = mock.patch.object(geromailer.connection, "close")
        closer.start()
        self.addCleanup(closer.stop)

    def _sent_message(self, in_reply_to, subject_override=None):
        sent = {}

        class Recorder:
            def __init__(self, *args, **kwargs):
                pass

            def login(self, user, password):
                return None

            def sendmail(self, sender, destination, raw):
                sent["raw"] = raw

            def close(self):
                return None

        payload = [self.report.report_id, self.report.report_title, "", "", ""]
        if subject_override is not None:
            patch_subject = mock.patch.dict(
                mail_templates.subjectlist, {202: subject_override})
            patch_subject.start()
            self.addCleanup(patch_subject.stop)
        with mock.patch.object(geromailer.smtplib, "SMTP_SSL", Recorder):
            geromailer.write_mail(202, payload, "hunter@example.com",
                                  in_reply_to=in_reply_to)
        return email.message_from_string(sent["raw"])

    def test_reply_carries_in_reply_to_and_both_references(self):
        msg = self._sent_message("<inbound-123@mail.example>")
        self.assertEqual(msg["In-Reply-To"], "<inbound-123@mail.example>")
        self.assertIn("<inbound-123@mail.example>", msg["References"])
        self.assertIn("<gerobug-report-" + self.report.report_id + "@example.com>",
                      msg["References"])

    def test_unsolicited_mail_still_carries_the_report_token(self):
        msg = self._sent_message(None)
        self.assertIsNone(msg["In-Reply-To"])
        self.assertEqual(
            msg["References"],
            "<gerobug-report-" + self.report.report_id + "@example.com>")

    def test_injected_newlines_never_reach_the_headers(self):
        msg = self._sent_message("<a@b>\r\nBcc: victim@example.com",
                                 subject_override="Status\r\nX-Injected: yes")
        self.assertNotIn("x-injected", [name.lower() for name in msg.keys()])
        self.assertNotIn("bcc", [name.lower() for name in msg.keys()])
        self.assertIsNone(msg["X-Injected"])
        self.assertIsNone(msg["Bcc"])
        for name, value in msg.items():
            with self.subTest(header=name):
                self.assertNotIn("\r", value)
                self.assertNotIn("\n", value)


class ReplyThreadingFlowTests(MailFlowTestCase):

    def test_read_mail_passes_the_inbound_message_id(self):
        report = make_report()
        self.deliver(raw_mail("CHECK_" + report.report_id))
        self.assertEqual(self.sent_codes(), [202])
        self.assertIn("in_reply_to", self.write_mail.call_args[1])
        self.assertTrue(self.write_mail.call_args[1]["in_reply_to"])
class MailFingerprintTests(SimpleTestCase):

    def _msg(self, **headers):
        msg = email.message.EmailMessage()
        for name, value in headers.items():
            msg[name.replace("_", "-")] = value
        msg.set_content("body text")
        return msg

    def test_message_id_drives_the_fingerprint(self):
        msg = self._msg(From="h@example.com", Message_ID="<abc@mail.example>")
        fingerprint = geroparser.mail_fingerprint(msg)
        self.assertRegex(fingerprint, r"^mid:[0-9a-f]{64}$")
        self.assertEqual(fingerprint, geroparser.mail_fingerprint(msg))

    def test_message_id_case_is_ignored(self):
        lower = self._msg(From="h@example.com", Message_ID="<abc@mail.example>")
        upper = self._msg(From="h@example.com", Message_ID="<ABC@MAIL.EXAMPLE>")
        self.assertEqual(geroparser.mail_fingerprint(lower),
                         geroparser.mail_fingerprint(upper))

    def test_folded_message_id_is_normalised(self):
        folded = geroparser.parse_raw_message(
            b"From: h@example.com\r\nMessage-ID: <abc\r\n @mail.example>"
            b"\r\nSubject: x\r\n\r\nbody")
        straight = self._msg(From="h@example.com", Message_ID="<abc@mail.example>")
        self.assertEqual(geroparser.mail_fingerprint(folded),
                         geroparser.mail_fingerprint(straight))

    def test_fingerprint_scoped_by_sender(self):
        mine = self._msg(From="hunter@example.com", Message_ID="<shared@mail.example>")
        theirs = self._msg(From="other@example.com", Message_ID="<shared@mail.example>")
        self.assertNotEqual(geroparser.mail_fingerprint(mine),
                            geroparser.mail_fingerprint(theirs))

    def test_missing_message_id_uses_content_hash(self):
        msg = self._msg(From="h@example.com", Date="Mon, 12 May 2025 10:00:00 +0200",
                        Subject="CHECK_AB12CD34EF56")
        fingerprint = geroparser.mail_fingerprint(msg)
        self.assertRegex(fingerprint, r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(fingerprint, geroparser.mail_fingerprint(msg))

    def test_content_hash_differs_per_message(self):
        a = self._msg(From="h@example.com", Subject="CHECK_AB12CD34EF56")
        b = self._msg(From="h@example.com", Subject="CHECK_CC11DD22EE33")
        self.assertNotEqual(geroparser.mail_fingerprint(a),
                            geroparser.mail_fingerprint(b))

    def test_overlong_message_id_fits_the_column(self):
        msg = self._msg(From="h@example.com",
                        Message_ID="<" + "a" * 400 + "@mail.example>")
        self.assertLessEqual(len(geroparser.mail_fingerprint(msg)), 128)


class IngestDedupeTests(MailFlowTestCase):

    def test_same_message_id_processed_once(self):
        report = make_report()
        raw = raw_mail("CHECK_" + report.report_id)
        self.deliver(raw)
        self.deliver(raw)
        self.assertEqual(self.sent_codes(), [202])
        self.assertEqual(ProcessedMail.objects.count(), 1)

    def test_distinct_mail_is_still_answered(self):
        report = make_report()
        self.deliver(raw_mail("CHECK_" + report.report_id))
        self.deliver(raw_mail("CHECK_" + report.report_id,
                              date="Tue, 13 May 2025 10:00:00 +0200"))
        self.assertEqual(self.sent_codes(), [202, 202])
        self.assertEqual(ProcessedMail.objects.count(), 2)

    def test_mail_without_a_message_id_dedupes_on_content(self):
        report = make_report()
        msg = MIMEMultipart("mixed")
        msg["From"] = "Hunter <hunter@example.com>"
        msg["Subject"] = "CHECK_" + report.report_id
        msg["Date"] = "Mon, 12 May 2025 10:00:00 +0200"
        msg["Return-Path"] = "<hunter@example.com>"
        msg.attach(MIMEText("", "plain"))
        raw = msg.as_bytes()
        self.deliver(raw)
        self.deliver(raw)
        self.assertEqual(self.sent_codes(), [202])
        row = ProcessedMail.objects.get()
        self.assertRegex(row.fingerprint, r"^sha256:[0-9a-f]{64}$")

    def test_a_submit_is_never_saved_twice(self):
        raw = raw_mail("SUBMIT_A good long title", body=SUBMIT_BODY, pdf=MINIMAL_PDF)
        self.deliver(raw)
        self.deliver(raw)
        self.assertEqual(self.sent_codes(), [201])
        self.assertEqual(BugReport.objects.count(), 1)

    def test_dedupe_runs_after_the_spoof_check(self):
        report = make_report()
        msg = MIMEMultipart("mixed")
        msg["From"] = "Hunter <hunter@example.com>"
        msg["Subject"] = "CHECK_" + report.report_id
        msg["Date"] = "Mon, 12 May 2025 10:00:00 +0200"
        msg["Message-ID"] = "<spoofed@example.com>"
        msg["Return-Path"] = "<someone.else@example.com>"
        msg.attach(MIMEText("", "plain"))
        self.deliver(msg.as_bytes())
        self.assertEqual(self.sent_codes(), [])
        self.assertFalse(ProcessedMail.objects.exists())

    def test_crash_after_claim_releases_fingerprint(self):
        report = make_report()
        raw = raw_mail("CHECK_" + report.report_id)
        self.write_mail.side_effect = RuntimeError("smtp exploded")
        self.deliver(raw)
        self.assertFalse(ProcessedMail.objects.exists())

        self.write_mail.side_effect = None
        self.write_mail.reset_mock()
        self.deliver(raw)
        self.assertEqual(self.sent_codes(), [202])
        self.assertEqual(ProcessedMail.objects.count(), 1)

    def test_a_refused_mail_stays_recorded(self):
        raw = raw_mail("CHECK_ZZ99YY88XX77")
        self.deliver(raw)
        self.deliver(raw)
        self.assertEqual(self.sent_codes(), [405])
        self.assertEqual(ProcessedMail.objects.count(), 1)

    def test_a_database_failure_does_not_drop_the_mail(self):
        report = make_report()
        with mock.patch.object(ProcessedMail.objects, "get_or_create",
                               side_effect=RuntimeError("boom")):
            self.deliver(raw_mail("CHECK_" + report.report_id))
        self.assertEqual(self.sent_codes(), [202])


class RetentionSweepTests(TestCase):

    def test_retention_sweep_keeps_recent_rows(self):
        now = timezone.now()
        ProcessedMail.objects.create(fingerprint="<old@example.com>",
                                     received_at=now - timedelta(days=181))
        ProcessedMail.objects.create(fingerprint="<edge@example.com>",
                                     received_at=now - timedelta(days=179))
        ProcessedMail.objects.create(fingerprint="<new@example.com>",
                                     received_at=now)
        self.assertEqual(geroparser.sweep_processed_mail(), 1)
        self.assertEqual(
            sorted(ProcessedMail.objects.values_list("fingerprint", flat=True)),
            ["<edge@example.com>", "<new@example.com>"])

    def test_retention_window_is_180_days(self):
        self.assertEqual(PROCESSED_MAIL_RETENTION_DAYS, 180)

    def test_sweep_is_gated_on_the_loop_count(self):
        source = inspect.getsource(geroparser.run)
        self.assertIn("loop_count % 2880 == 0", source)
        self.assertIn("sweep_processed_mail()", source)


class StatusStampTests(TestCase):

    def setUp(self):
        self.report = make_report(report_status=2)

    def test_status_change_stamps_time(self):
        self.assertIsNone(self.report.report_status_changed_at)
        report = BugReport.objects.get(report_id=self.report.report_id)
        report.report_status = 3
        report.save()
        report.refresh_from_db()
        self.assertIsNotNone(report.report_status_changed_at)
        self.assertLess(timezone.now() - report.report_status_changed_at,
                        timedelta(minutes=1))

    def test_save_with_update_fields_includes_stamp(self):
        report = BugReport.objects.get(report_id=self.report.report_id)
        report.report_status = 5
        report.save(update_fields=["report_status"])
        report.refresh_from_db()
        self.assertIsNotNone(report.report_status_changed_at)

    def test_non_status_save_does_not_stamp(self):
        report = BugReport.objects.get(report_id=self.report.report_id)
        report.report_title = "Renamed"
        report.save()
        report.refresh_from_db()
        self.assertIsNone(report.report_status_changed_at)


LEAK = "LEAKCHECK"


class CardTestCase(TestCase):

    def setUp(self):
        for status_id, name in enumerate(
                ["Invalid", "Received", "In Review", "Reproduced", "Fixing",
                 "Bounty Calculation", "Bounty in Process", "Completed"]):
            ReportStatus.objects.get_or_create(status_id=status_id,
                                               defaults={"status_name": name})
        MailBox.objects.get_or_create(mailbox_id=1,
                                      defaults={"email": "bounty@example.com"})


class MailtoTests(CardTestCase):

    def test_mailto_encodes_subject(self):
        link = gerocard.mailto("UPDATE", "AB12CD34EF56")
        self.assertEqual(link, "mailto:bounty@example.com?subject=UPDATE_AB12CD34EF56")

    def test_mailto_without_an_id(self):
        self.assertEqual(gerocard.mailto("HELP"),
                         "mailto:bounty@example.com?subject=HELP")

    def test_mailto_percent_encodes_a_dirty_id(self):
        link = gerocard.mailto("CHECK", "A B&C?D")
        self.assertNotIn(" ", link)
        self.assertNotIn("&", link)
        self.assertNotIn("?", link.split("?subject=", 1)[1])
        self.assertIn("A%20B%26C%3FD", link)

    def test_mailto_is_empty_without_a_mailbox(self):
        MailBox.objects.all().delete()
        self.assertEqual(gerocard.mailto("UPDATE", "AB12CD34EF56"), "")
        self.assertEqual(gerocard.render_actions("AB12CD34EF56", ["UPDATE"]), "")

    def test_render_actions_escapes_and_labels(self):
        actions = gerocard.render_actions("AB12CD34EF56", ["AGREE", "APPEAL"])
        self.assertIn("Agree to the decision", actions)
        self.assertIn("Appeal the decision", actions)
        self.assertIn("?subject=AGREE_AB12CD34EF56", actions)
        self.assertNotIn("<script", actions)


class ReportCardTests(CardTestCase):

    def card(self, **fields):
        return gerocard.build_report_card(make_report(**fields))

    def test_header_has_id_title_and_stage(self):
        card = self.card(report_status=2)
        self.assertIn("AB12CD34EF56", card)
        self.assertIn("Test finding", card)
        self.assertIn("Stage 2 of 7", card)
        self.assertIn("In Review", card)

    def test_missing_status_time_omits_since(self):
        self.assertNotIn("since", self.card(report_status=2))

    def test_status_time_shows_since(self):
        when = timezone.now() - timedelta(days=3)
        card = self.card(report_status=3, report_status_changed_at=when)
        self.assertIn("since " + when.strftime("%d %b %Y").lstrip("0"), card)

    def test_action_update_requested(self):
        report = make_report(report_status=2, report_permission=4,
                             last_email_code=701, last_email_note="Please add a PoC video link")
        card = gerocard.build_report_card(report)
        self.assertEqual(gerocard.action_needed(report)[0], "update")
        self.assertIn("asked you for more information", card)
        self.assertIn("Please add a PoC video link", card)
        self.assertIn("subject=UPDATE_AB12CD34EF56", card)

    def test_decision_deadline_names_the_agreement_rule(self):
        report = make_report(report_status=5, report_permission=2,
                             report_calc_sent_at=timezone.now())
        card = gerocard.build_report_card(report)
        self.assertIn("After that date the decision counts as agreed.", card)

    def test_action_decision_shows_severity_and_deadline(self):
        report = make_report(report_status=5, report_permission=2,
                             report_severity=7.5,
                             report_calc_sent_at=timezone.now())
        card = gerocard.build_report_card(report)
        self.assertEqual(gerocard.action_needed(report)[0], "decision")
        self.assertIn("High", card)
        self.assertIn("7.5", card)
        self.assertIn("subject=AGREE_AB12CD34EF56", card)
        self.assertIn("subject=APPEAL_AB12CD34EF56", card)

    def test_decision_section_has_no_money(self):
        report = make_report(report_status=5, report_permission=2,
                             report_calc_sent_at=timezone.now())
        card = gerocard.build_report_card(report).lower()
        for word in ("bounty amount", "usd", "$", "payout amount", "reward amount"):
            self.assertNotIn(word, card)

    def test_action_data_requested(self):
        report = make_report(report_status=6, report_permission=1,
                             last_email_code=703, last_email_note="Signed NDA and bank details")
        card = gerocard.build_report_card(report)
        self.assertEqual(gerocard.action_needed(report)[0], "data")
        self.assertIn("signed NDA is required", card)
        self.assertIn("Signed NDA and bank details", card)
        self.assertIn("subject=DATA_AB12CD34EF56", card)

    def test_action_closed(self):
        report = make_report(report_status=0, report_permission=0,
                             last_email_code=300, last_email_note="Out of scope endpoint")
        card = gerocard.build_report_card(report)
        self.assertEqual(gerocard.action_needed(report)[0], "closed")
        self.assertIn("closed as not valid", card)
        self.assertIn("Out of scope endpoint", card)

    def test_action_completed(self):
        report = make_report(report_status=7, report_permission=0)
        card = gerocard.build_report_card(report)
        self.assertEqual(gerocard.action_needed(report)[0], "completed")
        self.assertIn("certificate was emailed", card)

    def test_action_none(self):
        report = make_report(report_status=3, report_permission=0)
        card = gerocard.build_report_card(report)
        self.assertEqual(gerocard.action_needed(report)[0], "none")
        self.assertIn("Nothing is needed from you right now", card)

    def test_allowance_numbers(self):
        report = make_report(report_status=2, report_update_self=1, report_appeal=2)
        lines = gerocard.allowance_lines(report)
        self.assertIn("2 of 3", lines[0])
        self.assertIn("Appeals left: 1 of 3", lines[1])
        self.assertIn("2 of 3", gerocard.build_report_card(report))

    def test_allowances_closed_after_bounty_calculation(self):
        report = make_report(report_status=6)
        self.assertIn("Updates are closed", gerocard.allowance_lines(report)[0])

    def test_stage_explainer_matches_status(self):
        for status in range(0, 8):
            card = self.card(report_id="ST%09d" % status, report_status=status)
            self.assertIn(html.escape(gerocard.STAGE_TEXT[status]), card)

    def test_submissions_listed_oldest_first_with_pdf_flag(self):
        base = timezone.now() - timedelta(days=5)
        report = make_report(report_datetime=base)
        BugReportUpdate.objects.create(update_id="AB12CD34EF56U1",
                                       report_id=report.report_id,
                                       update_datetime=base + timedelta(days=1),
                                       update_summary="first", update_file=1)
        BugReportUpdate.objects.create(update_id="AB12CD34EF56U2",
                                       report_id=report.report_id,
                                       update_datetime=base + timedelta(days=3),
                                       update_summary="second", update_file=0)
        BugReportAppeal.objects.create(appeal_id="AB12CD34EF56A1",
                                       report_id=report.report_id,
                                       appeal_datetime=base + timedelta(days=2),
                                       appeal_summary="appeal", appeal_file=0)
        BugReportNDA.objects.create(nda_id="AB12CD34EF56N1",
                                    report_id=report.report_id,
                                    nda_datetime=base + timedelta(days=4),
                                    nda_summary="nda", nda_file=1)
        card = gerocard.build_report_card(report)
        order = [name for name in ("Original report", "AB12CD34EF56U1", "AB12CD34EF56A1",
                                   "AB12CD34EF56U2", "AB12CD34EF56N1")]
        positions = [card.index(name) for name in order]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(card.count(">yes<"), 3)
        self.assertEqual(card.count(">no<"), 2)

    def test_last_message_from_us(self):
        card = self.card(last_email_code=702, last_email_note="Severity set to High")
        self.assertIn("We sent you the bounty decision", card)
        self.assertIn("Severity set to High", card)

    def test_original_submission_block(self):
        card = self.card(report_attack="XSS", report_endpoint="https://example.com/a")
        self.assertIn("XSS", card)
        self.assertIn("https://example.com/a", card)

    def test_dates_are_plain(self):
        report = make_report(report_datetime=dt.datetime(2026, 10, 21, 9, 0,
                                                         tzinfo=dt.timezone.utc))
        card = gerocard.build_report_card(report)
        self.assertIn("21 Oct 2026", card)
        self.assertNotIn("\u2014", card)

    def test_title_with_html_is_escaped(self):
        report = make_report(report_title="<img src=x onerror=1>",
                             report_attack="<svg onload=alert(1)>",
                             report_endpoint="https://e.com/?a=<b>",
                             last_email_code=701,
                             last_email_note="<script>alert(1)</script>",
                             report_permission=4)
        card = gerocard.build_report_card(report)
        self.assertNotIn("<img", card)
        self.assertNotIn("<svg", card)
        self.assertNotIn("<script", card)
        self.assertIn("&lt;img src=x onerror=1&gt;", card)
        self.assertIn("&lt;script&gt;", card)

    def test_forbidden_fields_absent(self):
        report = make_report(
            report_status=5, report_permission=2,
            report_calc_sent_at=timezone.now(),
            report_reviewer=LEAK,
            report_duplicate=1,
            report_duplicate_of=LEAK[:15],
            report_severitystring="",
            report_severitytype=LEAK,
            report_summary=LEAK,
        )
        BugReport.objects.filter(report_id=report.report_id).update(
            report_severitystring=LEAK)
        report.refresh_from_db()
        card = gerocard.build_report_card(report)
        self.assertNotIn(LEAK, card)
        self.assertNotIn("bounty amount", card.lower())


class OverviewRowTests(CardTestCase):

    def test_overview_sorts_action_needed_first(self):
        old = timezone.now() - timedelta(days=10)
        make_report(report_id="AAAAAAAAAAAA", report_status=3, report_permission=0,
                    report_datetime=timezone.now())
        make_report(report_id="BBBBBBBBBBBB", report_status=2, report_permission=4,
                    report_datetime=old)
        rows = gerocard.build_overview_rows("hunter@example.com")
        self.assertEqual(len(rows), 2)
        self.assertIn("BBBBBBBBBBBB", rows[0])
        self.assertIn("AAAAAAAAAAAA", rows[1])
        self.assertIn("Send us more information", rows[0])
        self.assertIn(">-<", rows[1])

    def test_overview_newest_first_within_a_group(self):
        make_report(report_id="OLDOLDOLDOLD", report_status=3,
                    report_datetime=timezone.now() - timedelta(days=4))
        make_report(report_id="NEWNEWNEWNEW", report_status=3,
                    report_datetime=timezone.now())
        rows = gerocard.build_overview_rows("hunter@example.com")
        self.assertIn("NEWNEWNEWNEW", rows[0])
        self.assertIn("OLDOLDOLDOLD", rows[1])

    def test_overview_ids_link_to_check(self):
        make_report()
        row = gerocard.build_overview_rows("hunter@example.com")[0]
        self.assertIn("mailto:bounty@example.com?subject=CHECK_AB12CD34EF56", row)

    def test_overview_escapes_title(self):
        make_report(report_title="<img src=x onerror=1>")
        row = gerocard.build_overview_rows("hunter@example.com")[0]
        self.assertNotIn("<img", row)
        self.assertIn("&lt;img src=x onerror=1&gt;", row)

    def test_overview_without_a_mailbox_shows_plain_ids(self):
        MailBox.objects.all().delete()
        make_report()
        row = gerocard.build_overview_rows("hunter@example.com")[0]
        self.assertNotIn("mailto:", row)
        self.assertIn("AB12CD34EF56", row)

    def test_overview_only_the_senders_reports(self):
        make_report()
        make_report(report_id="CCCCCCCCCCCC", hunter_email="other@example.com")
        rows = gerocard.build_overview_rows("hunter@example.com")
        self.assertEqual(len(rows), 1)
        self.assertNotIn("CCCCCCCCCCCC", rows[0])


class StageTextTests(SimpleTestCase):

    def test_one_sentence_per_status(self):
        self.assertEqual(sorted(gerocard.STAGE_TEXT), list(range(0, 8)))
        for status, text in gerocard.STAGE_TEXT.items():
            self.assertTrue(text.endswith("."), status)
            self.assertNotIn("\u2014", text)
            self.assertNotIn("<", text)


class ActionsPlaceholderTests(CardTestCase):

    def setUp(self):
        super().setUp()
        MailBox.objects.all().update(email="bounty@example.com")

    def test_actions_placeholder_only_in_action_templates(self):
        for code, body in mail_templates.messagelist.items():
            if code in geromailer.ACTION_VERBS:
                self.assertIn("~ACTIONS~", body, code)
            else:
                self.assertNotIn("~ACTIONS~", body, code)

    def test_actions_rendered_for_each_action_code(self):
        for code, verbs in geromailer.ACTION_VERBS.items():
            actions = geromailer.render_actions_for(code, "AB12CD34EF56")
            for verb in verbs:
                self.assertIn("?subject=" + verb + "_AB12CD34EF56", actions, code)

    def test_actions_empty_for_other_codes(self):
        self.assertEqual(geromailer.render_actions_for(201, "AB12CD34EF56"), "")

    def test_actions_placeholder_never_left_raw(self):
        make_report()
        MailBox.objects.all().update(password="secret")
        closer = mock.patch.object(geromailer.connection, "close")
        closer.start()
        self.addCleanup(closer.stop)
        sent = []

        class Recorder:
            def __init__(self, *a, **kw):
                pass

            def login(self, *a):
                return None

            def sendmail(self, sender, destination, text):
                sent.append(text)

            def close(self):
                return None

        with mock.patch.object(geromailer.smtplib, "SMTP_SSL", Recorder):
            for code in sorted(mail_templates.messagelist):
                if code in (703, 704, 9999):
                    continue
                payload = ["AB12CD34EF56", "Test finding", 2, "note", "7.5"]
                geromailer.write_mail(code, payload, "hunter@example.com")
        self.assertTrue(sent)
        for text in sent:
            self.assertNotIn("~ACTIONS~", text)
            self.assertNotIn("~NOTE~", text)
            self.assertNotIn("~ID~", text)

    def test_actions_degrade_without_a_mailbox_address(self):
        MailBox.objects.all().update(email="")
        self.assertEqual(geromailer.render_actions_for(701, "AB12CD34EF56"), "")


class CheckCardFlowTests(MailFlowTestCase):

    def test_check_reply_contains_card(self):
        report = make_report(report_status=2, report_permission=4,
                             last_email_code=701, last_email_note="Add a PoC")
        self.deliver(raw_mail("CHECK_" + report.report_id))
        self.assertEqual(self.sent_codes(), [202])
        note = self.last_note()
        self.assertIn("Stage 2 of 7", note)
        self.assertIn("Test finding", note)
        self.assertIn("Add a PoC", note)
        self.assertIn("subject=UPDATE_" + report.report_id, note)

    def test_check_card_is_pre_rendered_html(self):
        self.assertEqual(geromailer.PRE_RENDERED_CODES, {202, 208, 210})

    def test_message_202_is_greeting_note_signoff(self):
        self.assertIn("~NOTE~", mail_templates.message_202)
        self.assertNotIn("~STATUS~", mail_templates.message_202)

    def test_check_card_escapes_a_hostile_title(self):
        report = make_report(report_title="<img src=x onerror=1>")
        self.deliver(raw_mail("CHECK_" + report.report_id))
        note = self.last_note()
        self.assertNotIn("<img", note)
        self.assertIn("&lt;img src=x onerror=1&gt;", note)

    def test_check_card_does_not_leak_triage_fields(self):
        report = make_report(report_reviewer=LEAK, report_duplicate_of="LEAKCHECK",
                             report_severitytype=LEAK, report_summary=LEAK)
        BugReport.objects.filter(report_id=report.report_id).update(
            report_severitystring=LEAK)
        self.deliver(raw_mail("CHECK_" + report.report_id))
        self.assertNotIn(LEAK, self.last_note())


class CheckCardDeliveryTests(CardTestCase):

    def test_check_card_survives_write_mail(self):
        report = make_report(report_status=2)
        MailBox.objects.all().update(email="bounty@example.com", password="secret")
        closer = mock.patch.object(geromailer.connection, "close")
        closer.start()
        self.addCleanup(closer.stop)
        sent = []

        class Recorder:
            def __init__(self, *a, **kw):
                pass

            def login(self, *a):
                return None

            def sendmail(self, sender, destination, text):
                sent.append(text)

            def close(self):
                return None

        card = gerocard.build_report_card(report)
        with mock.patch.object(geromailer.smtplib, "SMTP_SSL", Recorder):
            geromailer.write_mail(
                202, [report.report_id, report.report_title, 2, card, "7.5"],
                "hunter@example.com")
        self.assertTrue(sent)
        body = sent[0].replace("=\r\n", "").replace("=\n", "").replace("=3D", "=")
        self.assertIn("Stage 2 of 7", body)
        self.assertNotIn("&lt;table", body)


class OverviewFlowTests(MailFlowTestCase):

    def test_overview_sorts_action_needed_first_in_the_reply(self):
        make_report(report_id="AAAAAAAAAAAA", report_status=3,
                    report_datetime=timezone.now())
        make_report(report_id="BBBBBBBBBBBB", report_status=2, report_permission=4,
                    report_datetime=timezone.now() - timedelta(days=9))
        self.deliver(raw_mail("STATUS_OVERVIEW"))
        self.assertEqual(self.sent_codes(), [208])
        payload = self.last_payload()
        self.assertEqual(payload[0], "2")
        self.assertLess(payload[3].index("BBBBBBBBBBBB"),
                        payload[3].index("AAAAAAAAAAAA"))
        self.assertIn("Send us more information", payload[3])
        self.assertIn(">-<", payload[3])
        self.assertNotIn(">No<", payload[3])

    def test_overview_ids_link_to_check_in_the_reply(self):
        make_report()
        self.deliver(raw_mail("STATUS_OVERVIEW"))
        self.assertIn("mailto:bounty@example.com?subject=CHECK_AB12CD34EF56",
                      self.last_note())

    def test_overview_escapes_title_in_the_reply(self):
        make_report(report_title="<img src=x onerror=1>")
        self.deliver(raw_mail("STATUS_OVERVIEW"))
        note = self.last_note()
        self.assertNotIn("<img", note)
        self.assertIn("&lt;img src=x onerror=1&gt;", note)

    def test_overview_template_has_a_needs_you_column(self):
        self.assertIn("Needs you", mail_templates.message_208)

    def test_overview_for_a_sender_with_no_reports(self):
        self.deliver(raw_mail("STATUS_OVERVIEW", sender="nobody@example.com"))
        self.assertEqual(self.sent_codes(), [410])


class HelpTests(CardTestCase):

    def test_help_lists_every_command(self):
        help_html = gerocard.build_help("nobody@example.com")
        for verb, subject, description in gerocard.COMMAND_HELP:
            self.assertIn(subject, help_html, verb)
            self.assertIn(html.escape(description), help_html, verb)

    def test_help_for_unknown_sender_has_no_reports(self):
        make_report()
        help_html = gerocard.build_help("stranger@example.com")
        self.assertNotIn("AB12CD34EF56", help_html)
        self.assertNotIn("Your open reports", help_html)
        self.assertNotIn("Test finding", help_html)

    def test_help_lists_open_reports_only(self):
        make_report(report_id="AAAAAAAAAAAA", report_status=2,
                    report_title="Still open")
        make_report(report_id="BBBBBBBBBBBB", report_status=0,
                    report_title="Closed one")
        make_report(report_id="CCCCCCCCCCCC", report_status=7,
                    report_title="Finished one")
        help_html = gerocard.build_help("hunter@example.com")
        self.assertIn("AAAAAAAAAAAA", help_html)
        self.assertNotIn("BBBBBBBBBBBB", help_html)
        self.assertNotIn("CCCCCCCCCCCC", help_html)

    def test_help_never_shows_another_senders_report(self):
        make_report(report_id="AAAAAAAAAAAA", report_status=2,
                    hunter_email="someone@example.com", report_title=LEAK)
        help_html = gerocard.build_help("hunter@example.com")
        self.assertNotIn(LEAK, help_html)
        self.assertNotIn("AAAAAAAAAAAA", help_html)

    def test_help_states_the_allowances_of_each_open_report(self):
        make_report(report_status=2, report_update_self=1, report_appeal=1)
        help_html = gerocard.build_help("hunter@example.com")
        self.assertIn("Updates you can send on your own initiative: 2 of 3", help_html)
        self.assertIn("Appeals left: 2 of 3", help_html)

    def test_help_escapes_a_hostile_title(self):
        make_report(report_status=2, report_title="<img src=x onerror=1>")
        help_html = gerocard.build_help("hunter@example.com")
        self.assertNotIn("<img", help_html)
        self.assertIn("&lt;img src=x onerror=1&gt;", help_html)

    def test_help_buttons_need_no_report_id(self):
        help_html = gerocard.build_help("nobody@example.com")
        self.assertIn("?subject=STATUS_OVERVIEW", help_html)
        self.assertIn("?subject=MY_SCORE", help_html)
        self.assertNotIn("?subject=SUBMIT_", help_html)

    def test_help_without_a_mailbox_still_lists_the_commands(self):
        MailBox.objects.all().delete()
        help_html = gerocard.build_help("nobody@example.com")
        self.assertIn("STATUS_OVERVIEW", help_html)
        self.assertNotIn("mailto:", help_html)


class HelpFlowTests(MailFlowTestCase):

    def test_help_reply_is_code_210(self):
        self.deliver(raw_mail("HELP"))
        self.assertEqual(self.sent_codes(), [210])
        note = self.last_note()
        self.assertIn("STATUS_OVERVIEW", note)
        self.assertEqual(self.last_payload()[0], "")

    def test_help_is_pre_rendered(self):
        self.assertIn(210, geromailer.PRE_RENDERED_CODES)

    def test_help_reply_names_the_open_report(self):
        make_report(report_status=2)
        self.deliver(raw_mail("COMMANDS"))
        self.assertIn("AB12CD34EF56", self.last_note())

    def test_help_reply_to_an_unknown_sender_lists_no_reports(self):
        make_report(report_status=2)
        self.deliver(raw_mail("Re: help", sender="stranger@example.com"))
        self.assertEqual(self.sent_codes(), [210])
        self.assertNotIn("AB12CD34EF56", self.last_note())
