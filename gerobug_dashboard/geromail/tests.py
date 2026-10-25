import email

from django.test import SimpleTestCase

from geromail import gerocalculator, gerofilter, geromailer, geroparser


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
