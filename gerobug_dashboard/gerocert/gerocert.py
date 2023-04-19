import os
from PIL import Image, ImageDraw, ImageFont
from gerobug.settings import MEDIA_ROOT, BASE_DIR



def create_cert(id, name: str, certificate: str):
    img = Image.open(certificate, mode='r')
    image_width = img.width
    image_height = img.height
    draw = ImageDraw.Draw(img)

    font_name = 'ShareTechMono-Regular.ttf'
    font_path = os.path.join(BASE_DIR,'gerocert','font',font_name)
    font = ImageFont.truetype(font_path, 70)

    text_y_position = 740
    text_width, _ = draw.textsize(name, font=font)

    draw.text(
        (
            (image_width - text_width) / 2,
            text_y_position
        ),
        name,
        font=font,
        fill="#000")

    cert_name = id+"-C.jpg"
    cert_path = os.path.join(MEDIA_ROOT,id,cert_name)
    img.save(cert_path, format='JPEG')


def generate(id, name):
    CERTIFICATE = os.path.join(BASE_DIR,'gerocert',"Template_Cert.jpg")
    create_cert(id, name, CERTIFICATE)
