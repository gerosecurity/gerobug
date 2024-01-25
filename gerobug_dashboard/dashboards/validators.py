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