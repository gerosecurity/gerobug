import email
import imaplib
import time
import hashlib
import random
import re
import logging
from logging.handlers import TimedRotatingFileHandler
from email.utils import parsedate_tz, mktime_tz
from datetime import datetime

import gerocert.gerocert
from . import gerosecure
from . import gerofilter
from . import geromailer
from . import geronotify
from dashboards.models import BugHunter, BugReport, BugReportUpdate, BugReportAppeal, BugReportNDA
from prerequisites.models import MailBox
from gerobug.settings import MEDIA_ROOT



# IMAP CONFIG
EMAIL           = ""
PWD             = ""
IMAP_SERVER     = ""
IMAP_PORT       = 0

MAILBOX_READY   = False
PARSER_RUNNING  = False


# GENERATE REPORT ID
def generate_id(email, ts):
    hashed = hashlib.md5(email.encode())
    p1 = hashed.hexdigest()[0:4].upper()
    p2 = str(ts)[-4:]
    p3 = str(random.randint(1000,9999))
    id = p1 + p2 + p3
    
    return id


# INSERT USER TO BUGHUNTER MODEL
def saveuser(email, name, score):
    if BugHunter.objects.filter(hunter_email=email).exists():
        logging.getLogger("Gerologger").warning("User already exists.")
        pass
    else:
        if len(name) > 30:
            name = name[:30]

        newuser = BugHunter()
        newuser.hunter_email = email
        newuser.hunter_username = name
        newuser.hunter_scores = score

        newuser.save()
        logging.getLogger("Gerologger").info("New User registered.")


# INSERT NEW REPORT TO BUGREPORT MODEL
def savereport(id, email, date, title, atk_type, endpoint, summary):
    newreport = BugReport()
    
    newreport.report_id = id
    newreport.hunter_email = email
    newreport.report_datetime = date
    newreport.report_title = title
    newreport.report_attack = atk_type
    newreport.report_endpoint = endpoint
    newreport.report_summary = summary
    newreport.report_status = 1

    newreport.save()


# INSERT NEW UAN TO DATABASE
def save_uan(type, id, report_id, date, summary, file):
    if type == 'U':
        newupdate = BugReportUpdate()
        
        newupdate.update_id = id
        newupdate.report_id = report_id
        newupdate.update_datetime = date
        newupdate.update_summary = summary

        newupdate.save()
    
    elif type == 'A':
        newappeal = BugReportAppeal()
        
        newappeal.appeal_id = id
        newappeal.report_id = report_id
        newappeal.appeal_datetime = date
        newappeal.appeal_summary = summary
        newappeal.appeal_file = file

        newappeal.save()
    
    elif type == 'N':
        newNDA = BugReportNDA()
        
        newNDA.nda_id = id
        newNDA.report_id = report_id
        newNDA.nda_datetime = date
        newNDA.nda_summary = summary

        newNDA.save()


# READ INBOX (UNSEEN) AND PARSE DATA
def read_mail():
    try:
        # LOGIN TO IMAP / MAIL SERVER
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL,PWD)
        
        # READ DATA FROM INBOX
        mail.select('inbox')
        data = mail.search(None, 'UNSEEN') # data = mail.search(None, 'ALL')
        mail_ids = data[1]
        id_list = mail_ids[0].split()   

        # ITERATE THROUGH LIST OF EMAILS
        if(id_list):
            first_email_id = int(id_list[0])
            latest_email_id = int(id_list[-1])

            for i in range(first_email_id, latest_email_id+1):
                data = mail.fetch(str(i), '(RFC822)' )
                for response_part in data:
                    arr = response_part[0]

                    # EMAIL EXISTS
                    if isinstance(arr, tuple):
                        msg = email.message_from_string(str(arr[1],'utf-8'))

                        # DATETIME FORMATTING
                        msg_dt = parsedate_tz(msg['date'])
                        msg_ts = mktime_tz(msg_dt) #timestamps
                        email_dt = datetime.fromtimestamp(msg_ts)
                        email_date = email_dt.strftime("%Y-%m-%d %H:%M:%S")

                        # PARSE HUNTER NAME, EMAIL, AND SUBJECT
                        raw_from = str(msg['from'])
                        separator = raw_from.find(' <')

                        hunter_email = re.search(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", raw_from).group()
                        hunter_name = raw_from[:separator]
                        if len(hunter_name) < 3:
                            at = hunter_email.find('@')
                            hunter_name = hunter_email[:at]
                        email_subject = msg['subject']

                        logging.getLogger("Gerologger").info('============================')
                        logging.getLogger("Gerologger").info('NEW EMAIL RECEIVED!')
                        logging.getLogger("Gerologger").info('Time : ' + str(email_date))
                        logging.getLogger("Gerologger").info('From : ' + str(hunter_email) + ' (' + str(hunter_name) + ')')
                        logging.getLogger("Gerologger").info('Subject : ' + str(email_subject))
                        
                        # AVOID SELF LOOP                        
                        if hunter_email == EMAIL:
                            logging.getLogger("Gerologger").warning('Self Email, Ignoring Mail!')
                            continue

                        # NO-REPLY EXCLUSIONS
                        no_reply = re.search(r".*n.?t?.*reply.*@(.+\.)+.+", str(hunter_email))
                        if no_reply != None:
                            logging.getLogger("Gerologger").warning('No-reply emails, Ignoring Mail!')
                            continue

                        # SPOOF PREVENTION
                        spoof_check = re.search(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", str(msg['return-path']))
                        if spoof_check != None:
                            spoof_check = spoof_check.group()
                            if hunter_email != spoof_check:
                                logging.getLogger("Gerologger").warning('Possible Spoofing Attempt, Ignoring Mail!')
                                continue
                        else:
                            logging.getLogger("Gerologger").warning('Possible Spoofing Attempt, Ignoring Mail!')
                            continue
                        
                        # MONITOR SPAM ACTIVITY
                        gerosecure.monitor(hunter_email, int(msg_ts))
                        
                        # CHECK IF EMAIL BLACKLISTED
                        blacklisted, note, inform = gerosecure.check_blacklist(hunter_email)
                        if blacklisted:
                            # NOTIFY USER IF BLACKLISTED (ONLY ONCE)
                            if inform:
                                payload = ["","","",str(note),""] # ID, TITLE, STATUS, NOTE, SEVERITY
                                geromailer.write_mail(406, payload, hunter_email)
                                
                            continue
                        
                        # CLASSIFY ACTION AND SEND EMAIL NOTIFICATION
                        payload = ["","","","",""] # ID, TITLE, STATUS, NOTE, SEVERITY
                        code, payload[0] = gerofilter.classify_action(hunter_email, email_subject)

                        # HUNTER SUBMIT REPORT
                        if(code == 201):
                            report_id = generate_id(hunter_email, int(msg_ts))
                            report_title = payload[0]

                            # BUILD PAYLOAD FOR GEROMAIL
                            payload[0] = report_id
                            payload[1] = report_title

                            # CHECK ATTACHMENT AND PARSE BODY
                            have_attachment = gerofilter.validate_attachment(msg, report_id, MEDIA_ROOT)
                            if have_attachment:
                                msg_body = msg.get_payload()[0].get_payload()
                                if type(msg_body) is list:
                                    email_body = str(msg_body[0])
                                else:
                                    email_body = str(msg_body)
                                    
                                # CLEAN ENCODING FROM OUTLOOK
                                email_body = email_body.replace('=\n','')
                                email_body = email_body.replace('=3D','=')

                                logging.getLogger("Gerologger").info('Body : ' + str(email_body) + '\n')
                                atk_type, report_endpoint, report_summary = gerofilter.parse_body(email_body)
                                logging.getLogger("Gerologger").info('Title : ' + str(report_title))
                                logging.getLogger("Gerologger").info('Type : ' + str(atk_type))
                                logging.getLogger("Gerologger").info('Endpoint : ' + str(report_endpoint))
                                
                                # VALIDATE REPORT
                                if (len(report_title) < 3) or (atk_type == '') or (report_endpoint == '') or (len(report_summary) < 10):
                                    logging.getLogger("Gerologger").warning('[ERROR 404] Report not valid (Details are too short)')
                                    code = 404
                                    payload[3] = "Details are too short, make sure Title at least < 3, and Summary at least < 10"
                                    
                                elif (len(report_title) > 100) or (len(atk_type) > 100) or (len(report_endpoint) > 100):
                                    logging.getLogger("Gerologger").warning('[ERROR 404] Report not valid (Details are too long)')
                                    code = 404
                                    payload[3] = "Details are too long, make sure title, type, and endpoint are less than 100."
                                    
                                else:
                                    saveuser(hunter_email, str(hunter_name), 0)
                                    savereport(report_id, hunter_email, email_date, report_title, atk_type, report_endpoint, report_summary)
                                    
                                    gerofilter.check_duplicate(report_id)
                                    geronotify.notify(report_title, hunter_email, "NEW_REPORT")
                                    
                                    logging.getLogger("Gerologger").info('[CODE 201] Bug Hunter Report Saved Successfully')

                            else: 
                                email_body = msg.get_payload()[0].get_payload()
                                logging.getLogger("Gerologger").info('Body : ' + str(email_body) + '\n')
                                logging.getLogger("Gerologger").warning('[ERROR 404] Report not valid (Does not have attachment)')
                                code = 404
                                payload[3] = "Don't forget to attach a valid PDF file."
                                
                        # HUNTER CHECK STATUS
                        elif(code == 202): 
                            logging.getLogger("Gerologger").info('Report ID: ' + str(payload[0]))
                            report = BugReport.objects.get(report_id=payload[0])

                            payload[1] = report.report_title
                            payload[2] = report.report_status
                            logging.getLogger("Gerologger").info('[CODE 202] Bug Hunter Check Report Status')
                        
                        # HUNTER UPDATE/AMEND REPORT
                        elif(code == 203):
                            logging.getLogger("Gerologger").info('Report ID : ' + str(payload[0]))
                            report = BugReport.objects.get(report_id=payload[0])

                            # UPDATE COUNTER
                            report.report_update += 1
                            report.save()

                            # GENERATE UPDATE ID
                            update_id = str(payload[0]) + "U" + str(report.report_update)
                            logging.getLogger("Gerologger").info('Update ID : ' + str(update_id))

                            # CHECK ATTACHMENT AND PARSE BODY
                            have_attachment = gerofilter.validate_attachment(msg, update_id, MEDIA_ROOT)
                            if have_attachment:
                                # REVOKE PERMISSION AND UPDATE COUNTER
                                report.report_permission = report.report_permission - 4
                                report.save()

                                payload[1] = report.report_title

                                msg_body = msg.get_payload()[0].get_payload()
                                update_summary = re.sub(r"Content-T.*\n", "", str(msg_body[0]))
                                logging.getLogger("Gerologger").info('Update Summary : ' + str(update_summary) + '\n')

                                save_uan('U', update_id, str(payload[0]), email_date, update_summary, 0)
                                geronotify.notify(str(payload[0]), hunter_email, "NEW_UPDATE")
                                logging.getLogger("Gerologger").info('[CODE 203] Bug Hunter Update Saved Successfully')

                            else:
                                # UPDATE COUNTER ROLLBACK
                                report.report_update -= 1
                                report.save()

                                logging.getLogger("Gerologger").warning('[ERROR 404] Update not valid')
                                code = 404
                                payload[3] = "Update file not valid."

                        # HUNTER APPEAL REPORT
                        elif(code == 204):
                            logging.getLogger("Gerologger").info('Report ID : ' + str(payload[0]))
                            report = BugReport.objects.get(report_id=payload[0])

                            # UPDATE COUNTER
                            report.report_appeal += 1 
                            report.save()

                            payload[1] = report.report_title
                            
                            # GENERATE APPEAL ID
                            appeal_id = str(payload[0]) + "A" + str(report.report_appeal)
                            logging.getLogger("Gerologger").info('Appeal ID : ' + str(appeal_id))
                            
                            # CHECK ATTACHMENT AND PARSE BODY
                            have_attachment = gerofilter.validate_attachment(msg, appeal_id, MEDIA_ROOT)
                            if have_attachment:
                                msg_body = msg.get_payload()[0].get_payload()
                                appeal_summary = msg_body[0]
                                appeal_file = 1
                            else: 
                                appeal_summary = msg.get_payload()[0].get_payload()
                                appeal_file = 0

                            appeal_summary = re.sub(r"Content-T.*\n", "", str(appeal_summary))
                            logging.getLogger("Gerologger").info('Appeal Summary : ' + str(appeal_summary) + '\n')

                            # VALIDATE APPEAL
                            if len(appeal_summary) > 3:
                                # REVOKE PERMISSION AND UPDATE COUNTER
                                report.report_permission = report.report_permission - 2
                                report.save()

                                save_uan('A', appeal_id, str(payload[0]), email_date, appeal_summary, appeal_file)
                                geronotify.notify(str(payload[0]), hunter_email, "NEW_APPEAL")
                                logging.getLogger("Gerologger").info('[CODE 204] Bug Hunter Appeal Received Successfully')
                            
                            else: 
                                # UPDATE COUNTER ROLLBACK
                                report.report_appeal -= 1
                                report.save()

                                logging.getLogger("Gerologger").warning('[ERROR 404] Appeal not valid')
                                code = 404
                                payload[3] = "Appeal not valid."

                        # HUNTER AGREE
                        elif(code == 205):
                            logging.getLogger("Gerologger").info('Report ID: ' + str(payload[0]))
                            report = BugReport.objects.get(report_id=payload[0])

                            # REVOKE PERMISSION AND UPDATE STATUS
                            report.report_permission = report.report_permission - 2
                            report.save()

                            report.report_status += 1
                            payload = [report.report_id, report.report_title, report.report_status, "", ""]
                            geromailer.notify(report.hunter_email, payload)
                            
                            report.save()

                            geronotify.notify(str(payload[0]), hunter_email, "NEW_AGREE")
                            logging.getLogger("Gerologger").info('[CODE 205] Bug Hunter Agree Received Successfully')

                        # HUNTER SUBMITTED NDA
                        elif(code == 206):
                            logging.getLogger("Gerologger").info('Report ID: ' + str(payload[0]))
                            report = BugReport.objects.get(report_id=payload[0])

                            # UPDATE COUNTER
                            report.report_nda += 1
                            report.save()

                            # GENERATE NDA ID
                            nda_id = str(payload[0]) + "N" + str(report.report_nda)
                            logging.getLogger("Gerologger").info('NDA ID : ' + str(nda_id))

                            # CHECK ATTACHMENT AND PARSE BODY
                            have_attachment = gerofilter.validate_attachment(msg, nda_id, MEDIA_ROOT)
                            if have_attachment:
                                # REVOKE PERMISSION AND UPDATE COUNTER
                                report.report_permission = report.report_permission - 1
                                report.save()

                                msg_body = msg.get_payload()[0].get_payload()
                                nda_summary = re.sub(r"Content-T.*\n", "", str(msg_body[0]))
                                logging.getLogger("Gerologger").info('NDA Summary : ' + str(nda_summary) + '\n')

                                save_uan('N', nda_id, str(payload[0]), email_date, nda_summary, 0)
                                geronotify.notify(str(payload[0]), hunter_email, "NEW_NDA")
                                logging.getLogger("Gerologger").info('[CODE 206] Bug Hunter NDA Received Successfully')
                            
                            else: 
                                # UPDATE COUNTER ROLLBACK
                                report.report_nda -= 1
                                report.save()

                                logging.getLogger("Gerologger").warning('[ERROR 404] NDA not valid')
                                code = 404
                                payload[3] = "NDA file not valid."

                        # HUNTER CHECK SCORE
                        elif(code == 207):
                            logging.getLogger("Gerologger").info('Hunter Score: ' + str(payload[0]))
                            payload[3] = payload[0]
                            logging.getLogger("Gerologger").info("[CODE 207] Bug Hunter Check Score Successfully")

                        # HUNTER CHECK ALL STATUS
                        elif(code == 208):
                            payload[3] = str(payload[0]).replace('[','').replace(']','').replace("'",'').replace(',','\n')
                            payload[0] = str(len(payload[0]))
                            logging.getLogger("Gerologger").info('Hunter Reports (' + payload[0] + '):\n' + payload[3])
                            logging.getLogger("Gerologger").info("[CODE 208] Bug Hunter Check All Status Successfully")

                        # INVALID REPORT ID
                        elif(code == 405):
                            logging.getLogger("Gerologger").warning('[ERROR 405] Report ID not valid')

                        # USER NOT AUTHORIZED
                        elif(code == 403):
                            logging.getLogger("Gerologger").warning('[ERROR 403] User are not authorized!')

                        # INVALID REPORT FORMAT
                        else:
                            logging.getLogger("Gerologger").warning('[ERROR 404] Report not valid')
                            payload[3] = "Wrong formatting."

                        logging.getLogger("Gerologger").info('============================')
                        geromailer.write_mail(code, payload, hunter_email)
                        
        else:
            logging.getLogger("Gerologger").debug('No new email...')            

        mail.logout()

    except Exception as e:
        logging.getLogger("Gerologger").error("Failed to Login = " + str(e))
    


# PARSE COMPANY REQUEST geroparser.request(id, note, 701/702/703)
def company_action(id, note, code):
    report = BugReport.objects.get(report_id=id)
    
    if code == 701: # REQUEST AMEND
        logging.getLogger("Gerologger").info('[CODE 701] Request Amend to Bug Hunter')
        if not gerofilter.validate_permission("U", id):
            report.report_permission = report.report_permission + 4 
            report.save()
        
    elif code == 702: # SEND BOUNTY CALCULATIONS
        logging.getLogger("Gerologger").info('[CODE 702] Send Bounty Calculations')
        if not gerofilter.validate_permission("A", id):
            report.report_permission = report.report_permission + 2
            report.save()
        
    elif code == 703: # REQUEST NDA and OTHERS
        logging.getLogger("Gerologger").info('[CODE 703] Request NDA and Other Requirements to Bug Hunter')
        if not gerofilter.validate_permission("N", id):
            report.report_permission = report.report_permission + 1
            report.save()

    elif code == 704: # SEND CERTIFICATE and BOUNTY PROOF TO HUNTER
        logging.getLogger("Gerologger").info('[CODE 704] Send Certificate and Bounty Proof to Bug Hunter')
        
        # GET HUNTER NAME AND GENERATE CERTIFICATE
        hunter_email = report.hunter_email
        hunter = BugHunter.objects.get(hunter_email=hunter_email)
        gerocert.gerocert.generate(id, hunter.hunter_username, int(report.report_severity))

        # UPDATE HUNTER SCORE
        hunter.hunter_scores += int(report.report_severity)
        hunter.save()

        # UPDATE REPORT STATUS TO COMPLETE
        report.report_status += 1
        report.save()

    payload = [id, report.report_title, report.report_status, note, report.report_severity]
    destination = report.hunter_email

    geromailer.write_mail(code, payload, destination)


# RUN GEROMAIL MODULES
def run():
    global EMAIL, PWD, MAILBOX_READY, PARSER_RUNNING, IMAP_SERVER, IMAP_PORT
    MAILBOX_READY = False
    error_count = 0

    if PARSER_RUNNING:
        logging.getLogger("Gerologger").warning("Geroparser already started.")
        return 0
    else:
        PARSER_RUNNING = True
        logging.getLogger("Gerologger").debug("[LOG] Geroparser started.")

    while PARSER_RUNNING:
        # LIMIT ERRORS TO AVOID BLACKLISTED BY MAIL SERVER
        if error_count >= 3:
            logging.getLogger("Gerologger").warning("Error Limit Reached!")
            mailbox = MailBox.objects.get(mailbox_id=1)
            mailbox.email = ""
            mailbox.password = ""
            mailbox.mailbox_status = 0
            mailbox.save()

        # WAIT UNTIL MAILBOX READY
        while not MAILBOX_READY:
            mailbox = MailBox.objects.get(mailbox_id=1)
            if mailbox.email == "" or mailbox.password == "":
                logging.getLogger("Gerologger").debug("Waiting for Mailbox Setup...")
                time.sleep(5)
            else:
                MAILBOX_READY = True
        
        # ONLY RUN WHILE MAILBOX READY
        while MAILBOX_READY:
            mailbox = MailBox.objects.get(mailbox_id=1)
            if mailbox.email == "" or mailbox.password == "":
                MAILBOX_READY = False
                break

            EMAIL       = mailbox.email
            PWD         = mailbox.password
            TYPE        = mailbox.mailbox_type

            if TYPE == "2":
                IMAP_SERVER     = "outlook.office365.com"
                IMAP_PORT       = 993
            else:
                IMAP_SERVER     = "imap.gmail.com"
                IMAP_PORT       = 993

            # TEST LOGIN (VALIDATE CREDENTIALS)
            if mailbox.mailbox_status == 0:
                mail = imaplib.IMAP4_SSL(IMAP_SERVER)
                try:
                    mail.login(EMAIL,PWD)

                except Exception as e:
                    error_count+=1
                    logging.getLogger("Gerologger").error("Credentials Failed = " + str(e) + "("  + str(error_count) + ")")
                    MAILBOX_READY = False
                    time.sleep(5)
                    break
            
                # IF NO ERROR, SET STATUS TO ACTIVE
                mailbox.mailbox_status = 1
                mailbox.save()

            read_mail()
            time.sleep(30)

# RECOVER LOSS FILES
def recover_loss_file(id, type):
    report_id = str(id[:12])
    recover = False

    report = BugReport.objects.get(report_id=report_id)
    hunter_email = str(report.hunter_email)
    report_title = str(report.report_title)

    try:
        # LOGIN TO IMAP / MAIL SERVER
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL,PWD)

        # READ DATA FROM INBOX
        mail.select('inbox')
        if mailbox.mailbox_type == "1": # GMAIL
            if type == None:
                SEARCH = "from:" + hunter_email + " subject:SUBMIT_" + report_title
            elif type == "U":
                SEARCH = "from:" + hunter_email + " subject:UPDATE_" + report_title
            elif type == "N":
                SEARCH = "from:" + hunter_email + " subject:NDA_" + report_title

            data = mail.search(None, r'X-GM-RAW "'+SEARCH+'"')

        else:
            if type == None:
                SEARCH = '(FROM "' + hunter_email + '" SUBJECT "SUBMIT_' + report_title + '")'
            elif type == "U":
                SEARCH = '(FROM "' + hunter_email + '" SUBJECT "UPDATE_' + str(report_id) + '")'
            elif type == "N":
                SEARCH = '(FROM "' + hunter_email + '" SUBJECT "NDA_' + str(report_id) + '")'

            data = mail.search(None, SEARCH)

        mail_ids = data[1]
        id_list = mail_ids[0].split()   

        # ITERATE THROUGH LIST OF EMAILS
        if(id_list):
            latest_email_id = int(id_list[-1])
            data = mail.fetch(str(latest_email_id), '(RFC822)' )

            for response_part in data:
                arr = response_part[0]

                # EMAIL EXISTS
                if isinstance(arr, tuple):
                    msg = email.message_from_string(str(arr[1],'utf-8'))
                    recover = gerofilter.validate_attachment(msg, id, MEDIA_ROOT) 
        else:
            logging.getLogger("Gerologger").error('SEARCHED EMAIL NOT FOUND = ' + str(SEARCH))  

        mail.logout()  

    except Exception as e:
        logging.getLogger("Gerologger").error("Failed to Login = " + str(e))

    if recover:
        logging.getLogger("Gerologger").info("Recovery Successful = " + str(id))
    else:
        logging.getLogger("Gerologger").error("Recovery Failed = " + str(id))

    return recover