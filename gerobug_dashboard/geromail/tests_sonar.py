import time
from email.message import Message

from django.test import SimpleTestCase

from . import gerofilter, geroparser


class ParserRuntimeTests(SimpleTestCase):
    def test_body_adversarial_lines(self):
        for line in (' ' * 65536, 'TYPE' + ' ' * 65536):
            with self.subTest(prefix=line[:4]):
                started = time.perf_counter()
                self.assertEqual(gerofilter.parse_body(line), ('', '', ''))
                elapsed = time.perf_counter() - started
                print(f'FIELD_LINE 64KB: {elapsed:.6f}s')
                self.assertLess(elapsed, 0.5)

    def test_body_supported_labels(self):
        for label in ('type:', 'TYPE -', '**TYPE**:', 'TYPE ='):
            with self.subTest(label=label):
                self.assertEqual(
                    gerofilter.parse_body(label + ' XSS\nENDPOINT: /login\nSUMMARY: ENDPOINT is affected'),
                    ('XSS', '/login', 'ENDPOINT is affected'))

    def test_body_line_cap(self):
        self.assertEqual(len(gerofilter.parse_body('SUMMARY=' + 'a' * 65536)[2]), 9992)

    def test_return_path_inputs(self):
        for value in ('<Hunter@Example.COM>', 'Hunter@Example.COM'):
            msg = Message()
            msg['Return-Path'] = value
            self.assertIsNone(geroparser.sender_auth_failure(msg, 'hunter@example.com'))
        for value in ('', '<>', 'garbage'):
            msg = Message()
            msg['Return-Path'] = value
            self.assertEqual(geroparser.sender_auth_failure(msg, 'hunter@example.com'),
                             'Possible Spoofing Attempt (no Return-Path), Ignoring Mail!')

    def test_return_path_adversarial(self):
        msg = Message()
        msg['Return-Path'] = 'a' * 65536
        started = time.perf_counter()
        result = geroparser.sender_auth_failure(msg, 'hunter@example.com')
        elapsed = time.perf_counter() - started
        print(f'RETURN_PATH 64KB: {elapsed:.6f}s')
        self.assertEqual(result, 'Possible Spoofing Attempt (no Return-Path), Ignoring Mail!')
        self.assertLess(elapsed, 0.5)

    def test_sender_adversarial(self):
        started = time.perf_counter()
        self.assertEqual(geroparser.parse_sender('a' * 65536), ('', ''))
        elapsed = time.perf_counter() - started
        print(f'PARSE_SENDER 64KB: {elapsed:.6f}s')
        self.assertLess(elapsed, 0.5)

    def test_sender_valid(self):
        self.assertEqual(geroparser.parse_sender('Hunter <Hunter@Example.COM>'),
                         ('Hunter', 'Hunter@Example.COM'))

    def test_sender_plus_address_and_subdomain(self):
        for address in ('hunter+report@example.com', 'hunter@research.example.com',
                        'hunter+report@research.example.com'):
            with self.subTest(address=address):
                self.assertEqual(geroparser.parse_sender('Hunter <' + address + '>'),
                                 ('Hunter', address))

    def test_sender_domain_does_not_consume_local_part_plus(self):
        self.assertEqual(geroparser.parse_sender('Hunter <hunter@example+tag.com>'),
                         ('Hunter', ''))


class CardByteParityTests(SimpleTestCase):
    def test_check_card_bytes(self):
        import hashlib
        from types import SimpleNamespace
        from unittest.mock import patch
        from . import gerocard

        report = SimpleNamespace(
            report_status=2, report_id='AB12CD34EF56', report_title='Test <finding>',
            report_status_changed_at=None, last_email_code=0, report_datetime=None,
            report_attack='XSS', report_endpoint='/<test>')
        with patch.object(gerocard, '_status_name', return_value='In Review'), \
                patch.object(gerocard, '_action_section', return_value='Action'), \
                patch.object(gerocard, 'allowance_lines', return_value=['Allowance']), \
                patch.object(gerocard, '_submission_rows', return_value=[
                    ('Original <report>', None, True), ('Update', None, False)]):
            card = gerocard.build_report_card(report)
        self.assertEqual(hashlib.sha256(card.encode()).hexdigest(),
                         '0baa9a8d6cae6d5e34c3e0a17ee32c39cb17d61bbd2b6c0010c59d4fa2a1efce')
