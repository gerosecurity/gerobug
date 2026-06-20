from django.db import models
from geromail.gerocrypto import encrypt_value, decrypt_value


class EncryptedTextField(models.TextField):

    def get_prep_value(self, value):
        if value is None:
            return value
        value = super().get_prep_value(value)
        if not value:
            return value
        return encrypt_value(value)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        if not value:
            return value
        return decrypt_value(value)

    def to_python(self, value):
        if value is None:
            return value
        value = super().to_python(value)
        if not value:
            return value
        if isinstance(value, str) and value.startswith('gAAAAA'):
            return decrypt_value(value)
        return value


class EncryptedCharField(models.CharField):

    def get_prep_value(self, value):
        if value is None:
            return value
        value = super().get_prep_value(value)
        if not value:
            return value
        return encrypt_value(value)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        if not value:
            return value
        return decrypt_value(value)

    def to_python(self, value):
        if value is None:
            return value
        value = super().to_python(value)
        if not value:
            return value
        if isinstance(value, str) and value.startswith('gAAAAA'):
            return decrypt_value(value)
        return value
