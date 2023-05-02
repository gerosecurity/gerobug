import os
import magic
from django.core.exceptions import ValidationError

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