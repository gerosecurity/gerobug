import smtplib
import os
import logging

from logging.handlers import TimedRotatingFileHandler
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from . import mail_templates
from dashboards.models import ReportStatus
from gerobug.settings import MEDIA_ROOT, BASE_DIR
from prerequisites.models import MailBox



# WRITE EMAIL REPLY (CONFIRMATIONS)
def write_mail(code, payload, Destination):
    try:
        subject = mail_templates.subjectlist[code]
        body = mail_templates.messagelist[code]

        # GET STATUS NAME
        status = "NULL"
        if payload[2] != '':
            if ReportStatus.objects.filter(status_id=payload[2]).exists():
                status = ReportStatus.objects.get(status_id=payload[2])
                status = status.status_name

        if payload[3] == None:
            payload[3] = "-"
            
        # REPLACE WILD CARDS
        subject = subject.replace("~ID~", payload[0])       #REPORT ID
        body = body.replace("~ID~", payload[0])             #REPORT ID
        body = body.replace("~TITLE~", payload[1])          #REPORT TITLE
        body = body.replace("~STATUS~", status)             #REPORT STATUS
        body = body.replace("~NOTE~", payload[3])           #REASON / NOTE
        body = body.replace("~SEVERITY~", str(payload[4]))  #SEVERITY

        # BUILD EMAIL MESSAGE
        mailbox = MailBox.objects.get(mailbox_id=1)
        message = MIMEMultipart("alternative")
        message["From"] = mailbox.email
        message["To"] = Destination
        message["Subject"] = subject
        message_body = MIMEText(body, "html")
        message.attach(message_body)

        # BOUNTY IN PROCESS (NDA)
        if code == 703:
            nda_filename = "Template_NDA.pdf"
            nda_filepath = os.path.join(BASE_DIR,"static/templates",nda_filename)
            nda_file = open(nda_filepath, 'rb')
 
            attachment = MIMEBase('application', 'pdf', Name=nda_filename)
            attachment.set_payload((nda_file).read())
            encoders.encode_base64(attachment)
            
            attachment.add_header('Content-Description', nda_filename)
            attachment.add_header('Content-Decomposition', 'attachment', filename=nda_filename)        # GMAIL
            attachment.add_header('Content-Disposition', 'attachment', filename=nda_filename)          # OUTLOOK

            message.attach(attachment)
        
        # COMPLETE (BOUNTY PROOF + CERTIFICATE)
        elif code == 704:
            cert_filename = payload[0]+"-C.jpg"
            cert_filepath = os.path.join(MEDIA_ROOT,payload[0],cert_filename)
            cert_file = open(cert_filepath, 'rb')
 
            attachment = MIMEBase('application', 'image/jpeg', Name=cert_filename)
            attachment.set_payload((cert_file).read())
            encoders.encode_base64(attachment)
            
            attachment.add_header('Content-Description', cert_filename)
            attachment.add_header('Content-Decomposition', 'attachment', filename=cert_filename)        # GMAIL
            attachment.add_header('Content-Disposition', 'attachment', filename=cert_filename)          # OUTLOOK
            
            message.attach(attachment)

        # SEND EMAIL
        mailbox     = MailBox.objects.get(mailbox_id=1)
        EMAIL       = mailbox.email
        PWD         = mailbox.password
        TYPE        = mailbox.mailbox_type

        # SMTP CONFIG
        if TYPE == "2":
            SMTP_SERVER = "smtp.office365.com"
            SMTP_PORT   = 587
        else:
            SMTP_SERVER = "smtp.gmail.com"
            SMTP_PORT   = 465

        if EMAIL == "" or PWD == "":
            pass
        else:
            try:
                connection = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
                connection.login(EMAIL, PWD)
                connection.sendmail(EMAIL, Destination, message.as_string())
                connection.close()
                
            except Exception as e:
                with smtplib.SMTP(host=SMTP_SERVER, port=SMTP_PORT) as server:
                    server.starttls()
                    server.login(EMAIL, PWD)
                    server.sendmail(EMAIL, Destination, message.as_string())
                    server.close()
    
        logging.getLogger("Gerologger").info('Sent Email Successfully')

    except Exception as e: 
        logging.getLogger("Gerologger").error(str(e))


# WRITE EMAIL NOTIFICATION / UPDATES
def notify(destination, payload):
    if(payload[2] == 0):
        write_mail(300, payload, destination) # NOTIFY INVALID + REASON
    else:
        write_mail(301, payload, destination) # NOTIFY STATUS UPDATE
    
    logging.getLogger("Gerologger").info('Sent Notification to ' + str(destination) + ' ' + str(payload))
