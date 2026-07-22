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
