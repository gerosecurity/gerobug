from django.core.management.base import BaseCommand
from prerequisites.models import MailBox, Webhook
from geromail.gerocrypto import encrypt_value, decrypt_value


class Command(BaseCommand):
    help = 'Encrypt existing plaintext sensitive data in the database'

    def handle(self, *args, **options):
        self.stdout.write("Starting encryption of existing data...\n")

        mailbox_count = 0
        for mailbox in MailBox.objects.all():
            if mailbox.password and not self._is_encrypted(mailbox.password):
                mailbox.save(update_fields=['password'])
                mailbox_count += 1
        self.stdout.write(f"  MailBox records encrypted: {mailbox_count}")

        webhook_count = 0
        for webhook in Webhook.objects.all():
            if webhook.webhook_handle and not self._is_encrypted(webhook.webhook_handle):
                webhook.save(update_fields=['webhook_handle'])
                webhook_count += 1
        self.stdout.write(f"  Webhook records encrypted: {webhook_count}")

        total = mailbox_count + webhook_count
        if total == 0:
            self.stdout.write(self.style.SUCCESS(
                "\nNo plaintext records found. All data is already encrypted (or empty)."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\nDone! Encrypted {total} record(s) successfully."
            ))

    def _is_encrypted(self, value):
        if not value:
            return False
        return isinstance(value, str) and value.startswith('gAAAAA')
