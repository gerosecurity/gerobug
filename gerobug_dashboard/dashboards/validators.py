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

def validate_is_pdf(file):
    custom_err = 'Only PDF is allowed.'
    valid_mime_types = ['application/pdf']
    file_mime_type = magic.from_buffer(file.read(2048), mime=True)
    if file_mime_type not in valid_mime_types:
        raise ValidationError(custom_err)
    valid_file_extensions = ['.pdf']
    ext = os.path.splitext(file.name)[1]
    if ext.lower() not in valid_file_extensions:
        raise ValidationError(custom_err)
    filesize = file.size
    if filesize > (20 * 1024 * 1024):
        raise ValidationError("PDF size must be lower than 20MB")

def validate_is_docx(file):
    custom_err = 'Only DOCX is allowed.'
    valid_mime_types = ['application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    file_mime_type = magic.from_buffer(file.read(2048), mime=True)
    if file_mime_type not in valid_mime_types:
        raise ValidationError(custom_err)
    valid_file_extensions = ['.docx']
    ext = os.path.splitext(file.name)[1]
    if ext.lower() not in valid_file_extensions:
        raise ValidationError(custom_err)
    filesize = file.size
    if filesize > (20 * 1024 * 1024):
        raise ValidationError("DOCX size must be lower than 20MB")
    
def validate_is_image(file):
    custom_err = 'Only image file is allowed.'
    valid_mime_types = ['image/png','image/jpeg','image/jpg']
    file_mime_type = magic.from_buffer(file.read(2048), mime=True)
    if file_mime_type not in valid_mime_types:
        raise ValidationError(custom_err)
    valid_file_extensions = ['.png','.jpeg','.jpg']
    ext = os.path.splitext(file.name)[1]
    if ext.lower() not in valid_file_extensions:
        raise ValidationError(custom_err)
    filesize = file.size
    if filesize > (10 * 1024 * 1024):
        raise ValidationError("Image file size must be lower than 10MB")