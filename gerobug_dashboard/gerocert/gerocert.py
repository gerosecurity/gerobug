import os, magic
from PIL import Image, ImageDraw, ImageFont
from gerobug.settings import MEDIA_ROOT, BASE_DIR
from dashboards.models import CertificateData
from datetime import date


def create_cert(name: str, certificate: str, severity):
    CertData = CertificateData.objects.get(cert_id=1)
    signature_path = os.path.join(BASE_DIR,'gerocert','cert_signature')
    logo_path = os.path.join(BASE_DIR,'static','logo.png')

    img = Image.open(certificate, mode='r')
    image_width = img.width
    image_height = img.height
    draw = ImageDraw.Draw(img)

    font_name = 'ShareTechMono-Regular.ttf'
    font_path = os.path.join(BASE_DIR,'gerocert','font',font_name)
    
    # AWARDEE NAME
    font = ImageFont.truetype(font_path, 140)
    text_width = draw.textlength(name, font=font)
    draw.text(
        (
            (image_width - text_width) / 2,
            (image_height) / 2.35 
        ),
        name,
        font=font,
        fill="#000")
    
    # SEVERITY
    font = ImageFont.truetype(font_path, 80)
    if severity < 4:
        severity = "LOW"
    elif severity < 7:
        severity = "MEDIUM"
    elif severity < 9:
        severity = "HIGH"
    elif severity >= 9:
        severity = "CRITICAL"
    
    text_width = draw.textlength(severity, font=font)
    draw.text(
        (
            (image_width - text_width) / 2,
            (image_height) / 1.7 
        ),
        severity,
        font=font,
        fill="#DA0037")
    
    # ISSUE DATE
    today = str(date.today())
    text_width = draw.textlength(today, font=font)
    draw.text(
        (
            (image_width - text_width) / 1.8,
            (image_height) / 1.5
        ),
        today,
        font=font,
        fill="#000")
    
    # OFFICER NAME
    font = ImageFont.truetype(font_path, 80)
    text_width = draw.textlength(CertData.officer_name, font=font)
    x_name = (image_width - text_width) / 1.175
    y_name = (image_height) / 1.175
    draw.text(
        (x_name,y_name),
        CertData.officer_name,
        font=font,
        fill="#000")
    
    # OFFICER TITLE
    font = ImageFont.truetype(font_path, 60)
    draw.text(
        (x_name,y_name+100),
        CertData.officer_title,
        font=font,
        fill="#000")
    
    # OFFICER SIGNATURE
    SIGNATURE = Image.open(signature_path)
    SIGNATURE = SIGNATURE.resize((int(image_width*20/100),int(image_height*15/100)),Image.Resampling.LANCZOS)
    
    # VALIDATE FORMAT
    file_mime_type = magic.from_file(signature_path, mime=True)
    if file_mime_type == "image/png":
        if SIGNATURE.mode is not 'RGBA':
            SIGNATURE.convert("RGBA")
        img.paste(SIGNATURE, (int(x_name-10), int(y_name-(SIGNATURE.height+50))), mask=SIGNATURE)
    elif file_mime_type == "image/jpeg" or file_mime_type == "image/jpg":
        img.paste(SIGNATURE, (int(x_name-10), int(y_name-(SIGNATURE.height+50))))


    # COMPANY LOGO
    LOGO = Image.open(logo_path)
    LOGO = LOGO.resize((int(image_width*25/100),int(image_height*10/100)),Image.Resampling.LANCZOS)

    # VALIDATE FORMAT
    file_mime_type = magic.from_file(logo_path, mime=True)
    if file_mime_type == "image/png":
        if LOGO.mode is not 'RGBA':
            LOGO.convert("RGBA")
        img.paste(LOGO, (int(image_width / 17), int(y_name-215)), mask=LOGO)
    elif file_mime_type == "image/jpeg" or file_mime_type == "image/jpg":
        img.paste(LOGO, (int(image_width / 17), int(y_name-215)))


    return img


def generate(id, name, severity):
    TEMPLATE_CERT = os.path.join(BASE_DIR,'static/templates',"Template_Cert.jpg")
    CERTIFICATE = create_cert(name, TEMPLATE_CERT, severity)

    cert_name = id+"-C.jpg"
    cert_path = os.path.join(MEDIA_ROOT,id,cert_name)
    CERTIFICATE.save(cert_path, format='JPEG')

def generate_sample():
    TEMPLATE_CERT = os.path.join(BASE_DIR,'static/templates',"Template_Cert.jpg")
    CERTIFICATE = create_cert("John Doe", TEMPLATE_CERT, 10)

    sample_path = os.path.join(BASE_DIR,'static/templates',"Sample_Cert.jpg")
    CERTIFICATE.save(sample_path, format='JPEG')
