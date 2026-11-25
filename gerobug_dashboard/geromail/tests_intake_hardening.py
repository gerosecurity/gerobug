"""Mail-intake hardening (reports 5365C079BAD4, B5F277882DB3, D5D16D93C90A)
and folded Subject headers."""
import email
import email.message
import time
from datetime import timedelta
from unittest import mock

from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from dashboards.models import Blacklist, BlacklistRule, BugHunter, BugReport, Personalization, Watchlist
from geromail import gerofilter, geromailer, geroparser, gerosecure
from geromail import tests as base
from prerequisites.models import MailBox


TRIGGER_TITLE = "WooCommerce lets any logged-in customer spoof other users tracking via admin sync"


def forged_bounce(sender="victim@example.com"):
    return base.POSTFIX_DSN.replace(
        "From: MAILER-DAEMON@mail.example.com (Mail Delivery System)", "From: " + sender).encode()


def folded(raw, subject, folded_subject):
    return raw.replace(b"Subject: " + subject.encode(), b"Subject: " + folded_subject.encode())


class BounceAccountingTests(base.MailFlowTestCase):

    def setUp(self):
        super().setUp()
        gerosecure._BOUNCE_ALERTS.clear()

    def test_forged_bounces_never_watch_or_blacklist_the_sender(self):
        self.deliver(*[forged_bounce()] * 15)
        self.assertFalse(Watchlist.objects.exists())
        self.assertFalse(Blacklist.objects.exists())

    def test_existing_blacklist_notice_is_not_consumed_by_a_bounce(self):
        Blacklist.objects.create(email="victim@example.com", time=int(time.time()))
        self.deliver(forged_bounce())
        self.assertEqual(Blacklist.objects.get().informed, 0)

    def test_bounce_alert_is_throttled_per_report(self):
        base.make_report("A3F120261234", hunter_email="hunter@example.org")
        self.deliver(base.POSTFIX_DSN.encode(), base.POSTFIX_DSN.encode())
        self.assertEqual(self.notify.call_count, 1)


class ReturnPathParseTests(SimpleTestCase):

    def _msg(self, return_path):
        msg = email.message.EmailMessage()
        msg["Return-Path"] = return_path
        return msg

    def test_quoted_local_part_does_not_pass_as_the_victim(self):
        self.assertIsNotNone(geroparser.sender_auth_failure(
            self._msg('<"victim@example.com"@attacker.example>'), "victim@example.com"))

    def test_plain_and_commented_return_paths_still_pass(self):
        self.assertIsNone(geroparser.sender_auth_failure(self._msg("<Victim@Example.com>"), "victim@example.com"))
        self.assertIsNone(geroparser.sender_auth_failure(self._msg("<x@y.com> (comment)"), "x@y.com"))
        self.assertIsNone(geroparser.sender_auth_failure(self._msg("<prvs=1234abcd=x@y.com>"), "x@y.com"))

    def test_trailing_text_after_the_address_is_rejected(self):
        self.assertIsNotNone(geroparser.sender_auth_failure(
            self._msg("victim@example.com.attacker.example\"@evil.test"), "victim@example.com"))


class NoReplyTests(SimpleTestCase):

    def test_no_reply_addresses(self):
        for local in ("noreply", "no-reply", "no_reply", "donotreply", "do-not-reply",
                      "notifications-noreply", "mailer.noreply.bot"):
            with self.subTest(local=local):
                self.assertTrue(geroparser.is_no_reply(local + "@example.com"))

    def test_ordinary_addresses(self):
        for address in ("reply@example.com", "johnny.replies@example.com", "hunter@noreply.example.com",
                        "anreply@example.com"):
            with self.subTest(address=address):
                self.assertFalse(geroparser.is_no_reply(address))

    def test_long_local_part_returns_quickly(self):
        start = time.monotonic()
        self.assertTrue(geroparser.is_no_reply("n" * 8192 + "@example.com"))
        self.assertLess(time.monotonic() - start, 0.01)


class SenderKeyCaseTests(TestCase):

    def setUp(self):
        BlacklistRule.objects.get_or_create(rule_id=1)

    def test_mixed_case_addresses_share_one_watchlist_row(self):
        gerosecure.monitor("Victim@Example.com", 100)
        gerosecure.monitor("victim@example.com", 101)
        self.assertEqual(list(Watchlist.objects.values_list("email", flat=True)), ["victim@example.com"])

    def test_blacklist_lookup_ignores_case(self):
        gerosecure.blacklist("Victim@Example.com")
        self.assertTrue(gerosecure.check_blacklist("VICTIM@example.com")[0])


class ReceivedTimestampTests(SimpleTestCase):

    def test_internaldate_is_used(self):
        response = ("OK", [(b'1 (INTERNALDATE "12-May-2025 10:00:00 +0200" RFC822 {3}', b"raw"), b")"])
        self.assertEqual(geroparser.received_timestamp(response), 1747036800)

    def test_future_internaldate_is_capped_at_now(self):
        response = ("OK", [(b'1 (INTERNALDATE "12-May-2099 10:00:00 +0000" RFC822 {3}', b"raw")])
        self.assertLessEqual(geroparser.received_timestamp(response), int(time.time()))

    def test_missing_internaldate_falls_back_to_now(self):
        before = int(time.time())
        self.assertGreaterEqual(geroparser.received_timestamp(("OK", [(b"1 (RFC822 {3}", b"raw")])), before)
        self.assertGreaterEqual(geroparser.received_timestamp(("NO", None)), before)


class BackdatedSubmitTests(base.MailFlowTestCase):

    def test_backdated_date_header_does_not_set_report_time(self):
        self.deliver(base.raw_mail("SUBMIT_Backdated finding", body=base.SUBMIT_BODY, pdf=base.MINIMAL_PDF,
                                   date="Mon, 06 Jan 2020 10:00:00 +0000"))
        self.assertEqual(self.sent_codes(), [201])
        self.assertGreater(BugReport.objects.get().report_datetime, timezone.now() - timedelta(minutes=5))

    def test_reverse_duplicate_write_skips_reports_past_review(self):
        seed = base.make_report("DD44EE55FF66", report_endpoint="example.com/a", report_attack="XSS",
                                report_status=3)
        backdated = base.make_report("AA11BB22CC33", report_endpoint="example.com/a", report_attack="XSS",
                                     report_datetime=timezone.now() - timedelta(days=2), report_status=1)
        gerofilter.check_duplicate(backdated.report_id)
        seed.refresh_from_db()
        self.assertEqual(seed.report_duplicate, 0)


class PublicHunterNameTests(TestCase):

    def test_reserved_and_look_alike_names_are_replaced(self):
        for name in ("admin", "аdmin", "r00t", "Security", "Ｇｅｒｏｂｕｇ"):
            with self.subTest(name=name):
                self.assertTrue(geroparser.public_hunter_name("h@example.com", name).startswith("hunter-"))

    def test_company_name_is_treated_as_a_brand(self):
        Personalization.objects.create(personalize_id=1, company_name="GERO SECURITY")
        self.assertTrue(geroparser.public_hunter_name("h@example.com", "GERO-SECURITY").startswith("hunter-"))

    def test_ordinary_names_are_kept(self):
        for name in ("James", "Mehmet", "Rootkit Rachel", "Badminton Pro", "Jane Researcher"):
            with self.subTest(name=name):
                self.assertEqual(geroparser.public_hunter_name("h@example.com", name), name)

    def test_name_taken_by_another_hunter_gets_a_suffix(self):
        BugHunter.objects.create(hunter_email="first@example.com", hunter_username="James", hunter_scores=0)
        name = geroparser.public_hunter_name("second@example.com", "james")
        self.assertNotEqual(name.casefold(), "james")
        self.assertTrue(name.startswith("james-"))

    def test_saveuser_matches_existing_hunter_case_insensitively(self):
        BugHunter.objects.create(hunter_email="hunter@example.com", hunter_username="Hunter", hunter_scores=0)
        geroparser.saveuser("Hunter@Example.com", "Other", 0)
        self.assertEqual(BugHunter.objects.count(), 1)


class FoldedSubjectTests(SimpleTestCase):

    def test_folded_header_is_unfolded_on_decode(self):
        self.assertEqual(geroparser.mail_header_decode("SUBMIT_a b\r\n c\r\n\td"), "SUBMIT_a b c d")

    def test_encoded_word_with_newline_is_collapsed(self):
        self.assertEqual(geroparser.mail_header_decode("=?UTF-8?Q?SUBMIT=5Fa=0Ab?="), "SUBMIT_a b")

    def test_folded_submit_classifies(self):
        subject = "SUBMIT_" + TRIGGER_TITLE.replace(" users ", " users\r\n ")
        self.assertEqual(gerofilter.parse_subject(subject), ("SUBMIT", TRIGGER_TITLE))

    def test_folded_update_reply(self):
        subject = "Re: UPDATE_AB12CD34EF56 | Action Required: Additional\r\n Info"
        self.assertEqual(gerofilter.parse_subject(subject), ("UPDATE", "AB12CD34EF56"))


class FoldedSubjectFlowTests(base.MailFlowTestCase):

    def test_folded_submit_is_stored_with_a_clean_title(self):
        title = TRIGGER_TITLE + " " + "x" * (gerofilter.FIELD_LIMITS["title"][1] - len(TRIGGER_TITLE) - 1)
        raw = base.raw_mail("SUBMIT_PLACEHOLDER", body=base.SUBMIT_BODY, pdf=base.MINIMAL_PDF)
        self.deliver(folded(raw, "SUBMIT_PLACEHOLDER", "SUBMIT_" + title.replace(" users ", " users\n ")))
        self.assertEqual(self.sent_codes(), [201])
        self.assertEqual(BugReport.objects.get().report_title, title)

    def test_known_verb_without_separator_gets_a_specific_reason(self):
        self.deliver(base.raw_mail("SUBMITXSS on login", body=base.SUBMIT_BODY))
        self.assertEqual(self.sent_codes(), [404])
        self.assertIn("starting with SUBMIT", self.last_note())


class OutboundSubjectTests(TestCase):

    def test_crlf_in_subject_cannot_inject_headers(self):
        MailBox.objects.update_or_create(mailbox_id=1, defaults={"email": "bounty@example.com", "password": "x"})
        with mock.patch.object(geromailer, "connection"), \
                mock.patch.object(geromailer.smtplib, "SMTP_SSL") as smtp:
            self.assertTrue(geromailer.write_mail_raw("a\r\nBcc: x@y.example", "<p>b</p>", "h@example.com"))
        sent = smtp.return_value.sendmail.call_args[0][2]
        headers = sent.split("\n\n", 1)[0]
        self.assertEqual(headers.count("Subject:"), 1)
        self.assertNotIn("\nBcc:", headers)
