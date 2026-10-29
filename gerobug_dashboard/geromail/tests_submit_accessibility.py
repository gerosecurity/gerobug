from html.parser import HTMLParser
from pathlib import Path
import unittest


class SubmitMarkupTests(unittest.TestCase):
    def test_readonly_fields_and_status_output(self):
        root = Path(__file__).resolve().parents[2]
        for app in ('gerobug_dashboard', 'gerobug_web'):
            with self.subTest(app=app):
                elements = []
                parser = HTMLParser()
                parser.handle_starttag = lambda tag, attrs: elements.append((tag, dict(attrs)))
                source = (root / app / 'templates' / 'submit.html').read_text()
                parser.feed(source)
                fields = [attrs for tag, attrs in elements if tag == 'textarea' and 'readonly' in attrs]
                self.assertTrue(fields)
                for attrs in fields:
                    self.assertTrue(attrs.get('aria-label'))
                outputs = [attrs for tag, attrs in elements if tag == 'output' and attrs.get('id') == 'reportIdHint']
                self.assertEqual(len(outputs), 1)
                self.assertEqual(outputs[0].get('for'), 'reportIdInput')
                self.assertNotIn('role', outputs[0])
                self.assertNotIn("getAttribute('data-", source)
