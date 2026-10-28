import smtplib
import os
import html
import logging
import time

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from email.mime.base import MIMEBase
from email import encoders
from django.db import connection

from . import mail_templates
from dashboards.models import ReportStatus, TroubleshootSettings
from gerobug.settings import MEDIA_ROOT, BASE_DIR
from prerequisites.models import MailBox

# RETRY CONFIGURATION
MAX_RETRIES = 3
RETRY_DELAYS = [0, 2, 4]  # seconds between retries

# FREEMAIL PROVIDERS (FOR MESSAGE-ID)
FREEMAIL = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com"}

# ALLOW A SMALL SET OF FORMATTING TAGS, ESCAPE EVERYTHING ELSE
ALLOWED_TAGS = ["br", "br/", "br /", "b", "/b", "strong", "/strong", "i", "/i"]

def safe_html_format(text):
    if text is None:
        return "-"
    escaped = "<br>".join(html.escape(str(text)).splitlines())
    for tag in ALLOWED_TAGS:
        escaped = escaped.replace("&lt;" + tag + "&gt;", "<" + tag + ">")
    return escaped



# WRITE EMAIL REPLY (CONFIRMATIONS)
def write_mail(code, payload, Destination):
    # Close stale DB connections when called from threads
    try:
        connection.close()
    except:
        pass

    # TROUBLESHOOTING: silently drop hunter-facing email while the sinkhole
    # is active (Settings > Troubleshooting). Callers still get True so their
    # own side effects (permission bumps, last_email_code bookkeeping) run
    # unaffected; only the SMTP hand-off is skipped.
    if TroubleshootSettings.objects.filter(settings_id=1, hunter_email_sinkhole=True).exists():
        logging.getLogger("Gerologger").warning(
            f"Email to hunter SUPPRESSED by sinkhole (troubleshooting mode) | "
            f"To: {Destination} | Template: {code}"
        )
        return True
    
    # MINT THE MESSAGE IDENTITY ONCE, OUTSIDE THE RETRY LOOP.
    # A retry has to re-send the *same* message. Without a Message-ID the relay
    # mints a new one on every submission, so when the transport already
    # accepted the message and only the acknowledgement was lost (slow upstream
    # relay, socket timeout), the retry arrives as a second email the receiving
    # server has no way to collapse — hunters see duplicate report emails.
    try:
        mailbox = MailBox.objects.get(mailbox_id=1)
        if not mailbox.email or "@" not in mailbox.email:
            # Keep the log string this case used to emit; operators grep for it.
            logging.getLogger("Gerologger").error("Mailbox is not ready.")
            return False
        email_domain = mailbox.email.split("@")[1]
        sending_domain = "localhost" if email_domain in FREEMAIL else email_domain
        msg_id = make_msgid(domain=sending_domain)
        msg_date = formatdate(localtime=True)
    except Exception as e:
        logging.getLogger("Gerologger").error(f"Failed to prepare message for {Destination}: {e}")
        return False

    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            # Wait before retry (first attempt has no delay)
            if attempt > 0:
                delay = RETRY_DELAYS[attempt] if attempt < len(RETRY_DELAYS) else RETRY_DELAYS[-1]
                logging.getLogger("Gerologger").warning(f"Email retry attempt {attempt + 1}/{MAX_RETRIES} in {delay}s for {Destination}")
                time.sleep(delay)
            
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

            # REPLACE WILD CARDS (ESCAPED TO PREVENT HTML INJECTION)
            subject = subject.replace("~ID~", payload[0])                       #REPORT ID
            body = body.replace("~ID~", html.escape(payload[0]))                #REPORT ID
            body = body.replace("~TITLE~", html.escape(payload[1]))             #REPORT TITLE
            body = body.replace("~STATUS~", html.escape(str(status)))           #REPORT STATUS
            # CODE 208 SUPPLIES HTML TABLE ROWS ALREADY ESCAPED IN GEROFILTER
            if code == 208:
                body = body.replace("~NOTE~", str(payload[3]))                  #PRE-ESCAPED HTML ROWS
            else:
                body = body.replace("~NOTE~", safe_html_format(payload[3]))     #REASON / NOTE
            body = body.replace("~SEVERITY~", html.escape(str(payload[4])))     #SEVERITY

            # BUILD EMAIL MESSAGE (identity fixed above so retries are the same message)
            message = MIMEMultipart("alternative")
            message["From"] = mailbox.email
            message["To"] = Destination
            message["Subject"] = subject
            message["Date"] = msg_date
            message["Message-ID"] = msg_id
            # RFC 3834: tells other auto-responders not to reply to us, so a
            # vacation responder or another ticketing system can't start a loop.
            message["Auto-Submitted"] = "auto-generated"
            message_body = MIMEText(body, "html")
            message.attach(message_body)

            # BOUNTY IN PROCESS (NDA)
            if code == 703:
                nda_filename = "Template_NDA.pdf"
                nda_filepath = os.path.join(BASE_DIR,"static/templates",nda_filename)
                with open(nda_filepath, 'rb') as nda_file:
                    attachment = MIMEBase('application', 'pdf', Name=nda_filename)
                    attachment.set_payload(nda_file.read())
                    encoders.encode_base64(attachment)
                    
                    attachment.add_header('Content-Description', nda_filename)
                    attachment.add_header('Content-Decomposition', 'attachment', filename=nda_filename)        # GMAIL
                    attachment.add_header('Content-Disposition', 'attachment', filename=nda_filename)          # OUTLOOK

                    message.attach(attachment)
            
            # COMPLETE (BOUNTY PROOF + CERTIFICATE)
            elif code == 704:
                cert_filename = payload[0]+"-C.jpg"
                cert_filepath = os.path.join(MEDIA_ROOT,payload[0],cert_filename)
                with open(cert_filepath, 'rb') as cert_file:
                    attachment = MIMEBase('application', 'image/jpeg', Name=cert_filename)
                    attachment.set_payload(cert_file.read())
                    encoders.encode_base64(attachment)
                    
                    attachment.add_header('Content-Description', cert_filename)
                    attachment.add_header('Content-Decomposition', 'attachment', filename=cert_filename)        # GMAIL
                    attachment.add_header('Content-Disposition', 'attachment', filename=cert_filename)          # OUTLOOK
                    
                    message.attach(attachment)

            # SEND EMAIL
            EMAIL       = mailbox.email
            PWD         = mailbox.password
            SMTP_SERVER = mailbox.mailbox_smtp
            SMTP_PORT   = mailbox.mailbox_smtp_port

            if EMAIL == "" or PWD == "":
                logging.getLogger("Gerologger").error("Mailbox is not ready.")
                return False
            
            # Try SMTP_SSL first, fallback to STARTTLS
            try:
                smtp_conn = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30)
                smtp_conn.login(EMAIL, PWD)
                smtp_conn.sendmail(EMAIL, Destination, message.as_string())
                smtp_conn.close()
                logging.getLogger("Gerologger").info(f"Sent Email Successfully | To: {Destination} | ReportID: {payload[0]} | Template: {code} | Connection: SMTP_SSL")
                return True
                
            except Exception as ssl_error:
                # Fallback to STARTTLS
                try:
                    with smtplib.SMTP(host=SMTP_SERVER, port=SMTP_PORT, timeout=30) as server:
                        server.starttls()
                        server.login(EMAIL, PWD)
                        server.sendmail(EMAIL, Destination, message.as_string())
                        logging.getLogger("Gerologger").info(f"Sent Email Successfully | To: {Destination} | ReportID: {payload[0]} | Template: {code} | Connection: STARTTLS")
                        return True
                except Exception as tls_error:
                    raise Exception(f"SSL failed: {ssl_error}, STARTTLS failed: {tls_error}")
    
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                logging.getLogger("Gerologger").warning(f"Email attempt {attempt + 1} failed for {Destination}: {e}")
            continue
    
    # All retries exhausted
    logging.getLogger("Gerologger").error(f"Failed to Send Email after {MAX_RETRIES} attempts to {Destination}: {last_error}")


def write_mail_raw(subject, body, destination):
    try:
        connection.close()
    except:
        pass

    try:
        mailbox = MailBox.objects.get(mailbox_id=1)
        EMAIL       = mailbox.email
        PWD         = mailbox.password
        SMTP_SERVER = mailbox.mailbox_smtp
        SMTP_PORT   = mailbox.mailbox_smtp_port

        if EMAIL == "" or PWD == "":
            logging.getLogger("Gerologger").error("Mailbox is not ready.")
            return False

        message = MIMEMultipart("alternative")
        message["From"] = EMAIL
        message["To"] = destination
        message["Subject"] = subject
        message["Date"] = formatdate(localtime=True)
        message["Message-ID"] = make_msgid()
        message.attach(MIMEText(body, "html"))

        try:
            smtp_conn = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30)
            smtp_conn.login(EMAIL, PWD)
            smtp_conn.sendmail(EMAIL, destination, message.as_string())
            smtp_conn.close()
            logging.getLogger("Gerologger").info(f"Sent raw email to {destination} | Subject: {subject}")
            return True

        except Exception as ssl_error:
            try:
                with smtplib.SMTP(host=SMTP_SERVER, port=SMTP_PORT, timeout=30) as server:
                    server.starttls()
                    server.login(EMAIL, PWD)
                    server.sendmail(EMAIL, destination, message.as_string())
                    logging.getLogger("Gerologger").info(f"Sent raw email to {destination} via STARTTLS | Subject: {subject}")
                    return True
            except Exception as tls_error:
                raise Exception(f"SSL failed: {ssl_error}, STARTTLS failed: {tls_error}")

    except Exception as e:
        logging.getLogger("Gerologger").error(f"Failed to send raw email to {destination}: {e}")
        return False


# WRITE EMAIL NOTIFICATION / UPDATES
def notify(destination, payload):
    if(payload[2] == 0):
        write_mail(300, payload, destination) # NOTIFY INVALID + REASON
    else:
        write_mail(301, payload, destination) # NOTIFY STATUS UPDATE
    
    logging.getLogger("Gerologger").info('Sent Notification to ' + str(destination) + ' ' + str(payload))
