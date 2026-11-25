import ssl
from unittest import mock

from django.test import TestCase, TransactionTestCase

from geromail import geroparser
from geromail.tests import FakeIMAP, make_report
from prerequisites.models import MailBox


class RecoveryTransportTests(TestCase):
    def test_recovery_uses_verified_tls_and_configured_port(self):
        report = make_report()
        MailBox.objects.create(mailbox_id=1, email='bounty@example.com',
                               mailbox_imap='mail.example.com', mailbox_imap_port=1993)
        fake = FakeIMAP([])
        with mock.patch.object(geroparser.imaplib, 'IMAP4_SSL', return_value=fake) as connect, \
                mock.patch.object(geroparser.os, 'makedirs'):
            geroparser.recover_loss_file(report.report_id, None)
        self.assertEqual(connect.call_args.args, ('mail.example.com', 1993))
        context = connect.call_args.kwargs['ssl_context']
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)
        self.assertEqual(connect.call_args.kwargs['timeout'], 30)


class RecoveryIdentityTests(TestCase):
    def test_unrelated_search_results_never_reach_attachment_storage(self):
        from geromail.tests import raw_mail, MINIMAL_PDF
        report = make_report(report_title='Original OR from:other@example.com')
        MailBox.objects.create(mailbox_id=1, email='bounty@example.com')
        for kind, subject in ((None, 'SUBMIT_' + report.report_title),
                              ('U', 'UPDATE_' + report.report_id),
                              ('N', 'DATA_' + report.report_id),
                              ('N', 'NDA_' + report.report_id),
                              ('A', 'APPEAL_' + report.report_id)):
            for sender, candidate in (('other@example.com', subject),
                                      (report.hunter_email, subject + 'WRONG')):
                with self.subTest(kind=kind, sender=sender, subject=candidate):
                    fake = FakeIMAP([raw_mail(candidate, sender=sender, pdf=MINIMAL_PDF)])
                    with mock.patch.object(geroparser.imaplib, 'IMAP4_SSL', return_value=fake), \
                            mock.patch.object(geroparser.os, 'makedirs'), \
                            mock.patch.object(geroparser.gerofilter, 'validate_attachment') as store:
                        self.assertFalse(geroparser.recover_loss_file(report.report_id, kind))
                        store.assert_not_called()


class CompletionSecurityTests(TestCase):
    def test_completion_is_single_transition_with_single_notification(self):
        from dashboards.models import BugHunter
        report = make_report(report_status=6, report_severity=5)
        hunter = BugHunter.objects.create(hunter_email=report.hunter_email, hunter_username='Hunter', hunter_scores=0)
        with mock.patch('geromail.geroparser.gerocert.gerocert.generate') as certificate, mock.patch.object(geroparser.geromailer, 'write_mail') as send:
            with self.captureOnCommitCallbacks(execute=True):
                geroparser.company_action(report.pk, '', 704)
                geroparser.company_action(report.pk, '', 704)
            report.refresh_from_db()
            hunter.refresh_from_db()
            self.assertEqual(report.report_status, 7)
            self.assertEqual(hunter.hunter_scores, 10)
            certificate.assert_called_once()
            send.assert_called_once()

    def test_stale_actions_do_not_mutate_or_notify(self):
        report = make_report(report_status=7)
        with mock.patch.object(geroparser.geromailer, 'write_mail') as send:
            with self.captureOnCommitCallbacks(execute=True):
                for code in (701, 702, 703, 705, 0):
                    geroparser.company_action(report.pk, 'stale', code)
            report.refresh_from_db()
            self.assertEqual(report.report_permission, 0)
            self.assertEqual(report.last_email_code, 0)
            send.assert_not_called()


class ResourceLimitTests(TestCase):
    def test_oversize_attachment_is_rejected_without_decode(self):
        from email.message import Message
        part = Message()
        part['Content-Type'] = 'application/pdf'
        part['Content-Disposition'] = 'attachment; filename=report.pdf'
        part['Content-Transfer-Encoding'] = 'base64'
        part.set_payload('A' * 160)
        original = part.get_payload
        def payload(*args, **kwargs):
            if kwargs.get('decode'):
                self.fail('oversize payload decoded')
            return original(*args, **kwargs)
        with mock.patch.object(geroparser.gerofilter, 'MAX_PDF_BYTES', 100), mock.patch.object(part, 'get_payload', side_effect=payload):
            self.assertEqual(geroparser.gerofilter.extract_pdf_sized(part)[1], 'too_large')

    def test_part_count_limit_precedes_decode(self):
        from email.mime.multipart import MIMEMultipart
        from email.message import Message
        message = MIMEMultipart()
        for _ in range(33):
            message.attach(Message())
        self.assertEqual(geroparser.gerofilter.extract_pdf_sized(message)[1], 'resource_limit')

    def test_raw_limit_precedes_parser(self):
        with mock.patch.object(geroparser, 'MAX_RAW_MESSAGE_BYTES', 10, create=True), mock.patch.object(geroparser.email, 'message_from_bytes') as parse:
            with self.assertRaises(ValueError):
                geroparser.parse_raw_message(b'x' * 11)
            parse.assert_not_called()


class FetchLimitTests(TestCase):
    def test_missing_size_fails_closed(self):
        fake = mock.Mock()
        fake.fetch.return_value = ('OK', [b'1 ()'])
        self.assertEqual(geroparser.bounded_fetch(fake, 1), ('NO', []))
        fake.fetch.assert_called_once_with('1', '(RFC822.SIZE)')

    def test_oversize_recovery_is_not_fetched(self):
        report = make_report()
        MailBox.objects.create(mailbox_id=1, email='bounty@example.com')
        fake = mock.Mock()
        fake.search.return_value = ('OK', [b'1'])
        fake.fetch.return_value = ('OK', [b'1 (RFC822.SIZE 41943041)'])
        with mock.patch.object(geroparser.imaplib, 'IMAP4_SSL', return_value=fake), mock.patch.object(geroparser.os, 'makedirs'):
            self.assertFalse(geroparser.recover_loss_file(report.pk, None))
        fake.fetch.assert_called_once_with('1', '(RFC822.SIZE)')


class CookieConfigurationTests(TestCase):
    def test_cookie_configuration_supports_https_and_explicit_local_http(self):
        import ast
        import os
        from pathlib import Path
        from gerobug import settings
        tree = ast.parse(Path(settings.__file__).read_text())
        assignments = [node for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ('SESSION_COOKIE_SECURE', 'CSRF_COOKIE_SECURE') for t in node.targets)]
        for value, expected in (('true', True), ('false', False)):
            namespace = {'os': os}
            with mock.patch.dict(os.environ, {'GEROBUG_SECURE_COOKIES': value}):
                exec(compile(ast.Module(body=assignments, type_ignores=[]), '<cookie settings>', 'exec'), namespace)
            self.assertEqual(namespace.get('SESSION_COOKIE_SECURE'), expected)
            self.assertEqual(namespace.get('CSRF_COOKIE_SECURE'), expected)


class CumulativeLimitTests(TestCase):
    def test_cumulative_limit_rejects_before_any_decoder(self):
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        message = MIMEMultipart()
        for _ in range(2):
            part = MIMEBase('application', 'pdf')
            part.set_payload('A' * 80)
            part['Content-Transfer-Encoding'] = 'base64'
            part['Content-Disposition'] = 'attachment; filename=report.pdf'
            message.attach(part)
        with mock.patch.object(geroparser.gerofilter, 'MAX_ATTACHMENT_BYTES', 100), mock.patch.object(geroparser.gerofilter, 'check_pdf') as check:
            self.assertEqual(geroparser.gerofilter.extract_pdf_sized(message)[1], 'resource_limit')
            check.assert_not_called()

    def test_fetch_size_limit_is_shared_by_intake(self):
        fake = mock.Mock()
        fake.fetch.return_value = ('OK', [b'1 (RFC822.SIZE 41943041)'])
        self.assertEqual(geroparser.bounded_fetch(fake, 1), ('NO', []))
        fake.fetch.assert_called_once_with('1', '(RFC822.SIZE)')


class RecoveryPositiveTests(TestCase):
    def test_normalized_reply_and_legacy_subjects(self):
        from geromail.tests import raw_mail, MINIMAL_PDF
        report = make_report(report_title='Café')
        MailBox.objects.create(mailbox_id=1, email='bounty@example.com')
        for kind, subject in ((None, 'Re: Fwd: SUBMIT_Café'), ('U', 'Re: UPDATE_' + report.pk),
                              ('N', 'Re: DATA_' + report.pk), ('N', 'Fw: NDA_' + report.pk)):
            with self.subTest(kind=kind, subject=subject):
                fake = FakeIMAP([raw_mail(subject, sender=report.hunter_email, pdf=MINIMAL_PDF)])
                with mock.patch.object(geroparser.imaplib, 'IMAP4_SSL', return_value=fake), mock.patch.object(geroparser.os, 'makedirs'), mock.patch.object(geroparser.gerofilter, 'validate_attachment', return_value=True) as store:
                    self.assertTrue(geroparser.recover_loss_file(report.pk, kind))
                    store.assert_called_once()

    def test_valid_candidate_not_hidden_by_wrong_nearest(self):
        from django.utils import timezone
        from geromail.tests import raw_mail, MINIMAL_PDF
        report = make_report()
        MailBox.objects.create(mailbox_id=1, email='bounty@example.com')
        valid = raw_mail('UPDATE_' + report.pk, sender=report.hunter_email, pdf=MINIMAL_PDF)
        wrong = raw_mail('UPDATE_' + report.pk, sender='wrong@example.com', pdf=MINIMAL_PDF)
        fake = FakeIMAP([wrong, valid])
        with mock.patch.object(geroparser.imaplib, 'IMAP4_SSL', return_value=fake), mock.patch.object(geroparser.os, 'makedirs'), mock.patch.object(geroparser.gerofilter, 'validate_attachment', return_value=True) as store, mock.patch.object(fake, 'fetch', wraps=fake.fetch) as fetch:
            self.assertTrue(geroparser.recover_loss_file(report.pk, 'U', timezone.now()))
            store.assert_called_once()
            self.assertFalse(any('HEADER.FIELDS' in call.args[1] for call in fetch.call_args_list))


class MalformedPartTests(TestCase):
    def test_invalid_base64_cannot_underestimate_raw_fallback(self):
        from email.message import Message
        part = Message()
        part['Content-Type'] = 'application/pdf'
        part['Content-Disposition'] = 'attachment; filename=report.pdf'
        part['Content-Transfer-Encoding'] = 'base64'
        part.set_payload('A' * 101)
        original = part.get_payload
        def payload(*args, **kwargs):
            if kwargs.get('decode'):
                self.fail('malformed oversized payload decoded')
            return original(*args, **kwargs)
        with mock.patch.object(geroparser.gerofilter, 'MAX_PDF_BYTES', 100), mock.patch.object(part, 'get_payload', side_effect=payload):
            self.assertEqual(geroparser.gerofilter.extract_pdf_sized(part)[1], 'too_large')

    def test_raw_nested_parts_rejected_during_parse(self):
        raw = b'Content-Type: message/rfc822\r\n\r\n' * 40 + b'body'
        with self.assertRaises(ValueError):
            geroparser.parse_raw_message(raw)

    def test_invalid_quoted_printable_rejected_without_decode(self):
        from email.message import Message
        part = Message()
        part['Content-Type'] = 'application/pdf'
        part['Content-Disposition'] = 'attachment; filename=report.pdf'
        part['Content-Transfer-Encoding'] = 'quoted-printable'
        part.set_payload('=Z' * 60)
        original = part.get_payload
        def payload(*args, **kwargs):
            if kwargs.get('decode'):
                self.fail('oversized quoted printable decoded')
            return original(*args, **kwargs)
        with mock.patch.object(geroparser.gerofilter, 'MAX_PDF_BYTES', 100), mock.patch.object(part, 'get_payload', side_effect=payload):
            self.assertEqual(geroparser.gerofilter.extract_pdf_sized(part)[1], 'too_large')


class CompletionTransactionTests(TransactionTestCase):
    def setUp(self):
        from dashboards.models import BugHunter
        self.report = make_report(report_status=6, report_severity=5)
        self.hunter = BugHunter.objects.create(hunter_email=self.report.hunter_email, hunter_username='Hunter', hunter_scores=0)

    def test_concurrent_completion_awards_actual_score_once(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import connections
        gate = Barrier(2)
        def complete():
            try:
                gate.wait(timeout=10)
                return geroparser.company_action(self.report.pk, '', 704)
            finally:
                connections.close_all()
        with mock.patch('geromail.geroparser.gerocert.gerocert.generate') as certificate, mock.patch.object(geroparser.geromailer, 'write_mail') as send:
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: complete(), range(2)))
            self.assertEqual(sorted(results), [False, True])
            certificate.assert_called_once()
            send.assert_called_once()
        self.report.refresh_from_db()
        self.hunter.refresh_from_db()
        self.assertEqual((self.report.report_status, self.report.report_score_awarded, self.hunter.hunter_scores), (7, 10, 10))

    def test_outer_rollback_sends_nothing_and_restores_score(self):
        from django.db import transaction
        with mock.patch('geromail.geroparser.gerocert.gerocert.generate') as certificate, mock.patch.object(geroparser.geromailer, 'write_mail') as send:
            with self.assertRaises(RuntimeError):
                with transaction.atomic():
                    self.assertTrue(geroparser.company_action(self.report.pk, '', 704))
                    raise RuntimeError('rollback')
            certificate.assert_not_called()
            send.assert_not_called()
        self.report.refresh_from_db()
        self.hunter.refresh_from_db()
        self.assertEqual((self.report.report_status, self.report.last_email_code, self.hunter.hunter_scores), (6, 0, 0))

    def test_failed_certificate_can_be_explicitly_resent(self):
        from django.contrib.auth.models import User
        from django.urls import reverse
        with mock.patch('geromail.geroparser.gerocert.gerocert.generate', side_effect=RuntimeError('certificate failed')), mock.patch.object(geroparser.geromailer, 'write_mail') as send:
            with self.assertRaises(RuntimeError):
                geroparser.company_action(self.report.pk, '', 704)
            send.assert_not_called()
        self.report.refresh_from_db()
        self.assertEqual((self.report.report_status, self.report.last_email_code), (7, 704))
        self.client.force_login(User.objects.create_superuser(username='admin', password='x', email='admin@example.com'))
        with mock.patch('dashboards.views.geroparser.check_mailbox_status', return_value=True), mock.patch('dashboards.views.gerocert.gerocert.generate') as certificate, mock.patch('dashboards.views.geromailer.write_mail') as send, mock.patch('django.db.connection.close'), mock.patch('dashboards.views.threading.Thread', side_effect=lambda target, args=(), **kwargs: mock.Mock(start=lambda: target(*args))):
            response = self.client.post(reverse('resend_email'), {'report_id': self.report.pk})
            self.assertEqual(response.status_code, 302)
            certificate.assert_called_once()
            send.assert_called_once()
            self.assertEqual(send.call_args.args[0], 704)
        self.hunter.refresh_from_db()
        self.assertEqual(self.hunter.hunter_scores, 10)


class ComposeCookieTests(TestCase):
    def test_dashboard_loads_documented_cookie_env_file(self):
        from pathlib import Path
        from gerobug import settings
        compose = (Path(settings.BASE_DIR).parent / 'docker-compose.yml').read_text()
        dashboard = compose.split('  dashboard:', 1)[1].split('  db:', 1)[0]
        self.assertIn('- ./gerobug_dashboard/secrets/gerobug_secret.env', dashboard)
        self.assertNotIn('GEROBUG_SECURE_COOKIES:', dashboard)
