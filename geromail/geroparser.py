import email
import imaplib
import time
import hashlib
import random
import re
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


# GMAIL IMAP CONFIG
EMAIL           = ""
PWD             = ""
MAILBOX_READY   = False
IMAP_SERVER     = "imap.gmail.com"
IMAP_PORT       = 993


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
        print("[LOG] User already exists.")
        pass
    else:
        newuser = BugHunter()

        newuser.hunter_email = email
        newuser.hunter_username = name
        newuser.hunter_scores = score

        newuser.save()
        print("[LOG] New User registered.")


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

                        # PARSE HUNTER EMAIL AND SUBJECT
                        hunter_email = re.search(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", str(msg['from'])).group()
                        at = hunter_email.find('@')
                        hunter_name = hunter_email[:at]
                        email_subject = msg['subject']

                        print('\n============================')
                        print('[LOG] NEW EMAIL RECEIVED!')
                        print('Time : ' + email_date)
                        print('From : ' + hunter_email)
                        print('Subject : ' + email_subject)
                        
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
                                email_body = msg_body[0]
                                email_body = str(email_body)

                                print('Body : ' + email_body + '\n')
                                atk_type, report_endpoint, report_summary = gerofilter.parse_body(email_body)
                                
                                # VALIDATE REPORT
                                if (len(report_title) < 3) or (atk_type == '') or (report_endpoint == '') or (len(report_summary) < 10):
                                    print('[ERROR 404] Report not valid')
                                    code = 404
                                else:
                                    saveuser(hunter_email, hunter_name, 0)
                                    savereport(report_id, hunter_email, email_date, report_title, atk_type, report_endpoint, report_summary)
                                    
                                    gerofilter.check_duplicate(report_id)
                                    geronotify.notify(report_title, hunter_email)
                                    
                                    print('[CODE 201] Bug Hunter Report Saved Successfully')

                            else: 
                                email_body = msg.get_payload()[0].get_payload()
                                print('Body : ' + str(email_body) + '\n')
                                print('[ERROR 404] Report not valid (Does not have attachment)')
                                code = 404
                                
                        # HUNTER CHECK STATUS
                        elif(code == 202): 
                            print('Report ID: ' + payload[0])
                            report = BugReport.objects.get(report_id=payload[0])

                            payload[1] = report.report_title
                            payload[2] = report.report_status
                            print('[CODE 202] Bug Hunter Check Report Status')
                        
                        # HUNTER UPDATE/AMEND REPORT
                        elif(code == 203):
                            print('Report ID : ' + payload[0])
                            report = BugReport.objects.get(report_id=payload[0])

                            # UPDATE COUNTER
                            report.report_update += 1
                            report.save()

                            # GENERATE UPDATE ID
                            update_id = str(payload[0]) + "U" + str(report.report_update)
                            print('Update ID : ' + update_id)

                            # CHECK ATTACHMENT AND PARSE BODY
                            have_attachment = gerofilter.validate_attachment(msg, update_id, MEDIA_ROOT)
                            if have_attachment:
                                # REVOKE PERMISSION AND UPDATE COUNTER
                                report.report_permission = report.report_permission - 4
                                report.save()

                                payload[1] = report.report_title

                                msg_body = msg.get_payload()[0].get_payload()
                                update_summary = str(msg_body[0]).replace('Content-Type: text/plain; charset="UTF-8"', '')
                                print('Update Summary : ' + update_summary + '\n')

                                save_uan('U', update_id, str(payload[0]), email_date, update_summary, 0)
                                print('[CODE 203] Bug Hunter Update Saved Successfully')

                            else:
                                # UPDATE COUNTER ROLLBACK
                                report.report_update -= 1
                                report.save()

                                print('[ERROR 404] Update not valid')
                                code = 404

                        # HUNTER APPEAL REPORT
                        elif(code == 204):
                            print('Report ID : ' + payload[0])
                            report = BugReport.objects.get(report_id=payload[0])

                            # UPDATE COUNTER
                            report.report_appeal += 1 
                            report.save()

                            payload[1] = report.report_title
                            
                            # GENERATE APPEAL ID
                            appeal_id = str(payload[0]) + "A" + str(report.report_appeal)
                            print('Appeal ID : ' + appeal_id)
                            
                            # CHECK ATTACHMENT AND PARSE BODY
                            have_attachment = gerofilter.validate_attachment(msg, appeal_id, MEDIA_ROOT)
                            if have_attachment:
                                msg_body = msg.get_payload()[0].get_payload()
                                appeal_summary = msg_body[0]
                                appeal_file = 1
                            else: 
                                appeal_summary = msg.get_payload()[0].get_payload()
                                appeal_file = 0

                            appeal_summary = str(appeal_summary).replace('Content-Type: text/plain; charset="UTF-8"', '')
                            print('Appeal Summary : ' + appeal_summary + '\n')

                            # VALIDATE APPEAL
                            if len(appeal_summary) > 3:
                                # REVOKE PERMISSION AND UPDATE COUNTER
                                report.report_permission = report.report_permission - 2
                                report.save()

                                save_uan('A', appeal_id, str(payload[0]), email_date, appeal_summary, appeal_file)
                                print('[CODE 204] Bug Hunter Appeal Received Successfully')
                            
                            else: 
                                # UPDATE COUNTER ROLLBACK
                                report.report_appeal -= 1
                                report.save()

                                print('[ERROR 404] Appeal not valid')
                                code = 404

                        # HUNTER AGREE
                        elif(code == 205):
                            print('Report ID: ' + payload[0])
                            report = BugReport.objects.get(report_id=payload[0])

                            # REVOKE PERMISSION AND UPDATE STATUS
                            report.report_permission = report.report_permission - 2
                            report.save()

                            report.report_status += 1
                            payload = [report.report_id, report.report_title, report.report_status, "", ""]
                            geromailer.notify(report.hunter_email, payload)
                            
                            report.save()

                            print('[CODE 205] Bug Hunter Agree Received Successfully')

                        # HUNTER SUBMITTED NDA
                        elif(code == 206):
                            print('Report ID: ' + payload[0])
                            report = BugReport.objects.get(report_id=payload[0])

                            # UPDATE COUNTER
                            report.report_nda += 1
                            report.save()

                            # GENERATE NDA ID
                            nda_id = str(payload[0]) + "N" + str(report.report_nda)
                            print('NDA ID : ' + nda_id)

                            # CHECK ATTACHMENT AND PARSE BODY
                            have_attachment = gerofilter.validate_attachment(msg, nda_id, MEDIA_ROOT)
                            if have_attachment:
                                # REVOKE PERMISSION AND UPDATE COUNTER
                                report.report_permission = report.report_permission - 1
                                report.save()

                                msg_body = msg.get_payload()[0].get_payload()
                                nda_summary = str(msg_body[0]).replace('Content-Type: text/plain; charset="UTF-8"', '')
                                print('NDA Summary : ' + nda_summary + '\n')

                                save_uan('N', nda_id, str(payload[0]), email_date, nda_summary, 0)
                                print('[CODE 206] Bug Hunter NDA Received Successfully')
                            
                            else: 
                                # UPDATE COUNTER ROLLBACK
                                report.report_nda -= 1
                                report.save()

                                print('[ERROR 404] NDA not valid')
                                code = 404

                        # HUNTER CHECK SCORE
                        elif(code == 207):
                            print('[LOG] Hunter Score: ' + payload[0])
                            payload[3] = payload[0]
                            print("[CODE 207] Bug Hunter Check Score Successfully")

                        # HUNTER CHECK ALL STATUS
                        elif(code == 208):
                            payload[3] = str(payload[0]).replace('[','').replace(']','').replace("'",'').replace(',','\n')
                            payload[0] = str(len(payload[0]))
                            print('[LOG] Hunter Reports (',payload[0],'):\n' + payload[3])
                            print("[CODE 208] Bug Hunter Check All Status Successfully")

                        # INVALID REPORT ID
                        elif(code == 405):
                            print('[ERROR 405] Report ID not valid')

                        # USER NOT AUTHORIZED
                        elif(code == 403):
                            print('[ERROR 403] User are not authorized!')

                        # INVALID REPORT FORMAT
                        else:
                            print('[ERROR 404] Report not valid')

                        print('============================\n')
                        geromailer.write_mail(code, payload, hunter_email)
                        
        else:
            print('[LOG] No new email')            

    except Exception as e:
        print(str(e))
    
    mail.logout()


# PARSE COMPANY REQUEST geroparser.request(id, note, 701/702/703)
def company_action(id, note, code):
    report = BugReport.objects.get(report_id=id)
    
    if code == 701: # REQUEST AMEND
        print('[CODE 701] Request Amend to Bug Hunter')
        if not gerofilter.validate_permission("U", id):
            report.report_permission = report.report_permission + 4 
            report.save()
        
    elif code == 702: # SEND BOUNTY CALCULATIONS
        print('[CODE 702] Send Bounty Calculations')
        if not gerofilter.validate_permission("A", id):
            report.report_permission = report.report_permission + 2
            report.save()
        
    elif code == 703: # REQUEST NDA and OTHERS
        print('[CODE 703] Request NDA and Other Requirements to Bug Hunter')
        if not gerofilter.validate_permission("N", id):
            report.report_permission = report.report_permission + 1
            report.save()

    elif code == 704: # SEND CERTIFICATE and BOUNTY PROOF TO HUNTER
        print('[CODE 704] Send Certificate and Bounty Proof to Bug Hunter')
        
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
    global EMAIL, PWD, MAILBOX_READY
    MAILBOX_READY = False
    error_count = 0
    
    while True:
        # LIMIT ERRORS TO AVOID BLACKLISTED BY MAIL SERVER
        if error_count >= 3:
            print("[LOG] Error Limit Reached!")
            mailbox = MailBox.objects.get(mailbox_id=1)
            mailbox.email = ""
            mailbox.password = ""
            mailbox.mailbox_status = 0
            mailbox.save()

        # WAIT UNTIL MAILBOX READY
        while not MAILBOX_READY:
            mailbox = MailBox.objects.get(mailbox_id=1)
            if mailbox.email == "" or mailbox.password == "":
                print("Waiting for Mailbox Setup...")
                time.sleep(5)
            else:
                MAILBOX_READY = True
        
        # ONLY RUN WHILE MAILBOX READY
        while MAILBOX_READY:
            mailbox = MailBox.objects.get(mailbox_id=1)
            EMAIL       = mailbox.email
            PWD         = mailbox.password

            # TEST LOGIN
            if mailbox.mailbox_status == 0:
                mail = imaplib.IMAP4_SSL(IMAP_SERVER)
                try:
                    mail.login(EMAIL,PWD)

                except Exception as e:
                    error_count+=1
                    print("[ERROR] Failed to Login =",e,"(",str(error_count),")")
                    MAILBOX_READY = False
                    time.sleep(5)
                    break
            
                # IF NO ERROR, SET STATUS TO ACTIVE
                mailbox.mailbox_status = 1
                mailbox.save()

            read_mail()
            time.sleep(10)