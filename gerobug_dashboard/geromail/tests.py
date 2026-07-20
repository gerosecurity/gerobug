import email

from django.test import SimpleTestCase

from geromail import gerofilter, geroparser


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
