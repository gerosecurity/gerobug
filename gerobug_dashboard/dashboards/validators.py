import os
import re
import magic
from django.core.exceptions import ValidationError


USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 30
RESERVED_USERNAMES = {
    'admin', 'administrator', 'root', 'superuser', 'sysadmin', 'system',
    'support', 'security', 'gerobug', 'geromin', 'postmaster', 'webmaster',
    'mailer-daemon', 'noreply', 'no-reply', 'null', 'undefined', 'me',
}


def validate_username(value):
    name = (value or "").strip()

    if len(name) < USERNAME_MIN_LENGTH or len(name) > USERNAME_MAX_LENGTH:
        raise ValidationError(
            f"Username must be between {USERNAME_MIN_LENGTH} and {USERNAME_MAX_LENGTH} characters."
        )
    if not re.match(r'^[A-Za-z0-9]', name):
        raise ValidationError("Username must start with a letter or a number.")
    if not re.search(r'[A-Za-z0-9]$', name):
        raise ValidationError("Username must end with a letter or a number.")
    if not re.match(r'^[A-Za-z0-9._-]+$', name):
        raise ValidationError("Username may only contain letters, numbers, and the . _ - characters.")
    if re.search(r'[._-]{2,}', name):
        raise ValidationError("Username cannot contain two separators (. _ -) in a row.")
    if name.lower() in RESERVED_USERNAMES:
        raise ValidationError("This username is reserved. Please choose another.")

def _validate_file(file, valid_mime_types, valid_file_extensions, max_mb, type_err, size_err):
    if magic.from_buffer(file.read(2048), mime=True) not in valid_mime_types:
        raise ValidationError(type_err)
    if os.path.splitext(file.name)[1].lower() not in valid_file_extensions:
        raise ValidationError(type_err)
    if file.size > max_mb * 1024 * 1024:
        raise ValidationError(size_err)

def validate_is_pdf(file):
    _validate_file(file, ['application/pdf'], ['.pdf'], 20,
                   'Only PDF is allowed.', 'PDF size must be lower than 20MB')

def validate_is_docx(file):
    _validate_file(file, ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
                   ['.docx'], 20,
                   'Only DOCX is allowed.', 'DOCX size must be lower than 20MB')

def validate_is_image(file):
    _validate_file(file, ['image/png', 'image/jpeg', 'image/jpg'], ['.png', '.jpeg', '.jpg'], 10,
                   'Only image file is allowed.', 'Image file size must be lower than 10MB')