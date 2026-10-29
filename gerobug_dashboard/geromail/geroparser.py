import email
import imaplib
import time
import re
import hashlib
import logging
import os
import secrets
import ssl
import traceback
from email.utils import parsedate_tz, mktime_tz, parseaddr
from email.header import decode_header
from datetime import datetime, timedelta
from unicodedata import normalize
from django.db import connection, transaction
from django.utils import timezone

import gerocert.gerocert
from . import gerocard
from . import gerosecure
from . import gerofilter
from . import geromailer
from . import geronotify
from dashboards.models import (APPEAL_WINDOW_DAYS, BOUNTY_CALC_STATUS,
                               PROCESSED_MAIL_RETENTION_DAYS, BugHunter, BugReport,
                               BugReportUpdate, BugReportAppeal, BugReportNDA,
                               ProcessedMail)
from prerequisites.models import MailBox
from gerobug.settings import MEDIA_ROOT


# IMAP CONFIG
EMAIL           = ""
PWD             = ""
IMAP_SERVER     = ""
IMAP_PORT       = 0

MAILBOX_READY   = False
PARSER_RUNNING  = False
ERROR_COUNT     = 0


def _get_ssl_context():
    ctx = ssl.create_default_context()
    return ctx


def read_submission(msg):
    body = rm_html_tags(extract_email_body(msg)).strip()
    pdf, reason = gerofilter.extract_pdf(msg)
    return body, pdf, reason


def parse_raw_message(raw):
    if isinstance(raw, bytes):
        return email.message_from_bytes(raw)
    return email.message_from_string(str(raw))


def message_timestamp(msg):
    parsed = parsedate_tz(msg.get('date') or '')
    if parsed is None:
        return int(time.time())
    try:
        return int(mktime_tz(parsed))
    except (OverflowError, ValueError, TypeError):
        return int(time.time())

def loop_sender_reason(hunter_email, our_email, auto_submitted=None):
    """Why auto-replying to this sender risks a mail loop, or "" if it is safe.

    Two Gerobug instances sharing a domain traded "Invalid Report Format"
    replies every poll cycle until one side stopped; any vacation or ticketing
    auto-responder can start the same ping-pong.

    Guards, cheapest first: our own address; a sender that declares itself
    automated (RFC 3834); then anything else on our own domain -- skipped when
    the mailbox is on a freemail provider, where "our domain" would be
    gmail.com and the guard would drop nearly every real hunter.
    """
    sender = (hunter_email or "").strip().lower()
    ours = (our_email or "").strip().lower()

    if sender and sender == ours:
        return "Self Email"

    auto = (auto_submitted or "no").strip().lower()
    if auto and not auto.startswith("no"):
        return f"Automated sender (Auto-Submitted: {auto})"

    our_domain = ours.split("@")[-1] if "@" in ours else ""
    if (our_domain and our_domain not in geromailer.FREEMAIL
            and sender.endswith("@" + our_domain)):
        return "Own-domain sender (loop guard)"

    return ""


_NUMERIC_ID_RE = re.compile(r"^[0-9]+([eE][0-9]+)?$")


def _mint_id():
    while True:
        candidate = secrets.token_hex(6).upper()
        if not _NUMERIC_ID_RE.match(candidate):
            return candidate


# GENERATE REPORT ID
def generate_id():
    for _ in range(10):
        id = _mint_id()
        if not BugReport.objects.filter(report_id=id).exists():
            return id
    return _mint_id()


_FINGERPRINT_WS = re.compile(r"\s+")


def mail_fingerprint(msg):
    _, sender = parse_sender(msg.get('from'))
    sender = str(sender or '').strip().lower()

    message_id = _FINGERPRINT_WS.sub('', str(msg.get('Message-ID') or ''))
    if message_id:
        seed = sender + "\n" + message_id.lower()
        return "mid:" + hashlib.sha256(seed.encode('utf-8', 'replace')).hexdigest()

    parts = [
        sender,
        str(msg.get('from') or ''),
        str(msg.get('date') or ''),
        str(msg.get('subject') or ''),
    ]
    try:
        body = msg.as_bytes()[:4096]
    except Exception:
        body = repr(msg.get_payload())[:4096].encode('utf-8', 'replace')
    digest = hashlib.sha256('|'.join(parts).encode('utf-8', 'replace') + b'|' + body)
    return "sha256:" + digest.hexdigest()


def claim_mail(msg):
    try:
        fingerprint = mail_fingerprint(msg)
    except Exception as e:
        logging.getLogger("Gerologger").warning(f"Could not fingerprint mail: {e}")
        return False, ''
    if not fingerprint:
        return False, ''
    try:
        _, created = ProcessedMail.objects.get_or_create(fingerprint=fingerprint)
    except Exception as e:
        logging.getLogger("Gerologger").warning(f"Ingest dedupe unavailable: {e}")
        return False, ''
    if not created:
        return True, ''
    return False, fingerprint


def already_processed(msg):
    seen, _ = claim_mail(msg)
    return seen


def release_fingerprint(fingerprint):
    if not fingerprint:
        return False
    try:
        deleted, _ = ProcessedMail.objects.filter(fingerprint=fingerprint).delete()
    except Exception as e:
        logging.getLogger("Gerologger").warning(
            f"Could not release ingest fingerprint {fingerprint}: {e}")
        return False
    return bool(deleted)


def sweep_processed_mail():
    cutoff = timezone.now() - timedelta(days=PROCESSED_MAIL_RETENTION_DAYS)
    deleted, _ = ProcessedMail.objects.filter(received_at__lt=cutoff).delete()
    if deleted:
        logging.getLogger("Gerologger").info(
            f"Pruned {deleted} ProcessedMail rows older than "
            f"{PROCESSED_MAIL_RETENTION_DAYS} days")
    return deleted


def _sanitize_imap_string(value):
    if not value:
        return ''
    return str(value).replace('"', '').replace('\\', '').replace('\r', '').replace('\n', '')


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
        newupdate.update_file = file

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
        newNDA.nda_file = file

        newNDA.save()


def mail_header_decode(text):
    if not text:
        return ""
    try:
        return u"".join([
            part.decode(encoding or 'utf-8', errors='replace') if isinstance(part, bytes) else part
            for part, encoding in decode_header(text)])
    except Exception:
        return str(text)


def parse_sender(raw_from):
    raw_from = str(raw_from or "")
    display_name, addr = parseaddr(raw_from)
    match = re.search(r"[\w\.\-+_]+@[\w\.\-+_]+\.[\w]+", addr or raw_from)
    email_address = match.group() if match else ""

    name = mail_header_decode(display_name)
    if len(name) < 3:
        name = email_address[:email_address.find('@')]

    return re.sub(r'[^\w\s\-]', '', name, flags=re.UNICODE).strip(), email_address


def sender_auth_failure(msg, hunter_email):
    auth_results = msg.get('Authentication-Results', '')
    if auth_results:
        spf_pass = bool(re.search(r'\bspf=pass\b', auth_results, re.IGNORECASE))
        dkim_pass = bool(re.search(r'\bdkim=pass\b', auth_results, re.IGNORECASE))
        if not (spf_pass or dkim_pass):
            return f'Spoofing blocked (SPF/DKIM failed): spf={spf_pass}, dkim={dkim_pass}, from={hunter_email}'

    return_path = re.search(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", str(msg.get('return-path', '')), re.IGNORECASE)
    if return_path is None:
        return 'Possible Spoofing Attempt (no Return-Path), Ignoring Mail!'
    if hunter_email.lower() != return_path.group().lower():
        return f'Possible Spoofing Attempt (Return-Path mismatch), Ignoring Mail! from={hunter_email}'
    return None


def parse_bounce(msg):
    # PULL THE FAILED RECIPIENT, SMTP ERROR AND ORIGINAL IDS OUT OF AN RFC 3464 DSN.
    # DSN VALUES ARE OFTEN FOLDED ACROSS LINES, SO THEY ARE READ AS HEADER BLOCKS
    # AND WHITESPACE-COLLAPSED RATHER THAN MATCHED PER LINE.
    info = {'failed_to': 'unknown', 'error': 'unknown', 'orig_msg_id': 'unknown', 'report_id': 'unknown'}
    try:
        for part in msg.walk():
            ptype = part.get_content_type()
            if ptype == 'message/delivery-status':
                for block in part.get_payload():
                    for key, field in (('failed_to', 'Final-Recipient'), ('error', 'Diagnostic-Code')):
                        value = block.get(field)
                        if value and info[key] == 'unknown':
                            info[key] = ' '.join(str(value).split(';', 1)[-1].split())
            elif ptype in ('message/rfc822', 'text/rfc822-headers'):
                orig = part.get_payload()
                orig = orig[0] if isinstance(orig, list) else email.message_from_string(str(orig))
                info['orig_msg_id'] = orig.get('Message-ID', 'unknown')
                m = re.search(r'\b([0-9A-F]{12})\b', mail_header_decode(orig.get('Subject') or ''))
                if m:
                    info['report_id'] = m.group(1)
    except Exception as e:
        logging.getLogger("Gerologger").debug(f"DSN parse error: {e}")
    return info


def bounce_matches_report(info):
    report = BugReport.objects.filter(report_id=str(info.get('report_id', ''))).only('hunter_email').first()
    return bool(report) and report.hunter_email.lower() == str(info.get('failed_to', '')).lower()


def rm_html_tags(text):
    text = text.replace('&nbsp;', '')
    text = re.sub(r'<br.*?>', '\n', text)
    text = re.sub(r'<div.*?>', '\n', text)
    text = re.sub(r'<.*?>', '', text)

    return text


def extract_email_body(msg):
    # Prefers text/plain over text/html, and within each keeps the last
    # NON-BLANK part seen.
    #
    # Non-blank matters: Apple Mail appends an empty trailing text/plain
    # part after an inline attachment, which used to overwrite the real
    # body with "" and fail every SUBMIT with "Details are too short".
    #
    # Plain-over-html matters: a multipart/alternative message pairs a
    # text/plain branch with a separate multipart/mixed branch holding
    # text/html + the inline attachment. Both texts are non-blank, so
    # picking whichever comes last in msg.walk() picked html half the
    # time -- and stripping tags off content like
    # "the <code>clientId</code> and" glues words together
    # ("theclientIdand") since the surrounding &nbsp; is stripped too.
    plain_body = ""
    html_body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            content_disp = str(part.get("Content-Disposition"))
            if "attachment" in content_disp:
                continue
            content_type = part.get_content_type()
            if content_type not in ('text/plain', 'text/html'):
                continue
            payload = part.get_payload(decode=True)
            if payload is None:
                continue
            charset = part.get_content_charset() or 'utf-8'
            try:
                text = payload.decode(charset, errors='ignore')
            except (LookupError, AttributeError):
                text = payload.decode('utf-8', errors='ignore')
            if not text.strip():
                continue
            if content_type == 'text/plain':
                plain_body = text
            else:
                html_body = text
        body = plain_body or html_body
    else:
        payload = msg.get_payload(decode=True)
        if payload is not None:
            charset = msg.get_content_charset() or 'utf-8'
            try:
                body = payload.decode(charset, errors='ignore')
            except (LookupError, AttributeError):
                body = payload.decode('utf-8', errors='ignore')
        else:
            body = ""

    return body

# GET SPAM FOLDER NAME DYNAMICALLY
def get_spam_folder(mail):
    try:
        typ, data = mail.list()
        for line in data:
            if isinstance(line, bytes):
                line = line.decode('utf-8')

            if any(keyword in line for keyword in ["Spam", "Junk", "Bin", "Trash"]):
                match = re.search(r'"([^"]+)"$', line)
                if match:
                    return match.group(1)
                else:
                    parts = line.split()
                    return parts[-1].replace('"', '')
    except Exception as e:
        logging.getLogger("Gerologger").warning(f"Failed to detect spam folder: {e}")
    return None


def check_connection_alive(mail):
    try:
        mail.noop()
        return True
    except (imaplib.IMAP4.abort, imaplib.IMAP4.error, OSError, Exception):
        return False

# READ INBOX (UNSEEN) AND PARSE DATA
def read_mail(mail, folder_name='inbox'):
    global ERROR_COUNT
    try:
        # SELECT FOLDER
        try:
            mail.select(folder_name)
        except imaplib.IMAP4.abort as abort_err:
            logging.getLogger("Gerologger").info(f"IMAP connection lost while selecting {folder_name}, will reconnect")
            raise abort_err
        except Exception as e:
            logging.getLogger("Gerologger").warning(f"Failed to select folder {folder_name}: {e}")
            raise e

        data = mail.search(None, 'UNSEEN') # data = mail.search(None, 'ALL')
        mail_ids = data[1]
        id_list = mail_ids[0].split()   

        ERROR_COUNT = 0

        # ITERATE THROUGH LIST OF EMAILS
        if(id_list):
            for i_str in id_list:
                claimed = ''
                try:
                    i = int(i_str)
                    data = mail.fetch(str(i), '(RFC822)' )
                    for response_part in data:
                        arr = response_part[0]

                        # EMAIL EXISTS
                        if isinstance(arr, tuple):
                            msg = parse_raw_message(arr[1])

                            # DATETIME FORMATTING
                            msg_ts = message_timestamp(msg)
                            email_dt = datetime.fromtimestamp(msg_ts)
                            email_date = email_dt.strftime("%Y-%m-%d %H:%M:%S")

                            # PARSE HUNTER NAME, EMAIL, AND SUBJECT
                            hunter_name, hunter_email = parse_sender(msg['from'])
                            
                            # email_subject = msg['subject']
                            email_subject = mail_header_decode(msg['subject'])

                            logging.getLogger("Gerologger").info('============================')
                            logging.getLogger("Gerologger").info(f'NEW EMAIL RECEIVED ({folder_name})!')
                            logging.getLogger("Gerologger").info('Time : ' + str(email_date))
                            logging.getLogger("Gerologger").info('From : ' + str(hunter_email) + ' (' + str(hunter_name) + ')')
                            logging.getLogger("Gerologger").info('Subject : ' + str(email_subject))
                            
                            # DETECT BOUNCE / DELIVERY STATUS NOTIFICATIONS (RFC 3464).
                            # MUST BE HANDLED BEFORE THE SPOOF / RETURN-PATH CHECKS, WHICH
                            # WOULD OTHERWISE SWALLOW THEM AS SPOOFING ATTEMPTS.
                            _return_path = str(msg.get('return-path', '')).strip()
                            _report_type = (msg.get_param('report-type') or '').lower()
                            _is_bounce = (
                                _report_type == 'delivery-status'
                                or bool(re.match(r'mailer-daemon@', hunter_email, re.IGNORECASE))
                                or re.match(r'^<\s*>$', _return_path) is not None
                            )
                            if _is_bounce:
                                b = parse_bounce(msg)
                                logging.getLogger("Gerologger").error(
                                    f"EMAIL DELIVERY FAILED | "
                                    f"BounceFrom: {hunter_email} | "
                                    f"FailedTo: {b['failed_to']} | "
                                    f"ReportID: {b['report_id']} | "
                                    f"Error: {b['error']} | "
                                    f"OriginalMsgID: {b['orig_msg_id']} | "
                                    f"Subject: {email_subject}"
                                )
                                blacklisted = bool(hunter_email) and gerosecure.check_blacklist(hunter_email)[0]
                                if hunter_email:
                                    gerosecure.monitor(hunter_email, int(msg_ts))
                                if not blacklisted and bounce_matches_report(b):
                                    geronotify.notify(b['report_id'], b['failed_to'], "EMAIL_BOUNCED", detail=b['error'])
                                else:
                                    logging.getLogger("Gerologger").warning(
                                        f"Bounce not matched to a report's hunter or sender rate-limited, webhook alert skipped | "
                                        f"ReportID: {b['report_id']} | FailedTo: {b['failed_to']}")
                                continue

                            # AVOID MAIL LOOPS (see loop_sender_reason)
                            _loop = loop_sender_reason(hunter_email, EMAIL, msg.get('Auto-Submitted'))
                            if _loop:
                                logging.getLogger("Gerologger").warning(
                                    f'{_loop}, Ignoring Mail! from={hunter_email}')
                                continue

                            # NO-REPLY EXCLUSIONS
                            no_reply = re.search(r".*n.?t?.*reply.*@(.+\.)+.+", str(hunter_email))
                            if no_reply != None:
                                logging.getLogger("Gerologger").warning('No-reply emails, Ignoring Mail!')
                                continue

                            # SPOOF PREVENTION
                            _spoof = sender_auth_failure(msg, hunter_email)
                            if _spoof:
                                logging.getLogger("Gerologger").warning(_spoof)
                                continue

                            seen, claimed = claim_mail(msg)
                            if seen:
                                logging.getLogger("Gerologger").warning(
                                    f'Already processed, Ignoring Mail! from={hunter_email} '
                                    f'subject={email_subject}')
                                continue

                            # MONITOR SPAM ACTIVITY
                            gerosecure.monitor(hunter_email, int(msg_ts))
                            
                            # CHECK IF EMAIL BLACKLISTED
                            blacklisted, note, inform = gerosecure.check_blacklist(hunter_email)
                            if blacklisted:
                                # NOTIFY USER IF BLACKLISTED (ONLY ONCE)
                                if inform:
                                    payload = ["","","",str(note),""] # ID, TITLE, STATUS, NOTE, SEVERITY
                                    geromailer.write_mail(406, payload, hunter_email,
                                                          in_reply_to=msg['Message-ID'])
                                    
                                continue
                            
                            # CLASSIFY ACTION AND SEND EMAIL NOTIFICATION
                            payload = ["","","","",""] # ID, TITLE, STATUS, NOTE, SEVERITY
                            code, payload[0] = gerofilter.classify_action(hunter_email, email_subject)

                            # HUNTER SUBMIT REPORT
                            if(code == 201):
                                report_title = str(payload[0]).strip()
                                payload[1] = report_title

                                email_body, report_pdf, pdf_reason = read_submission(msg)
                                reason = gerofilter.pdf_reason_text(
                                    pdf_reason, gerofilter.attachment_size(msg))
                                if not reason and report_pdf is None:
                                    reason = gerofilter.REASON_SUBMIT_NO_PDF

                                atk_type, report_endpoint, report_summary = gerofilter.parse_body(email_body)
                                if not reason:
                                    reason = gerofilter.validate_submit_fields(
                                        report_title, atk_type, report_endpoint, report_summary)

                                logging.getLogger("Gerologger").info('Title : ' + str(report_title))
                                logging.getLogger("Gerologger").info('Type : ' + str(atk_type))
                                logging.getLogger("Gerologger").info('Endpoint : ' + str(report_endpoint))

                                if reason:
                                    logging.getLogger("Gerologger").warning(
                                        '[ERROR 404] Report not valid: ' + reason)
                                    code = 404
                                    payload[0] = ""
                                    payload[3] = reason

                                else:
                                    report_id = generate_id()
                                    payload[0] = report_id

                                    saveuser(hunter_email, str(hunter_name), 0)
                                    savereport(report_id, hunter_email, email_date, report_title,
                                               atk_type, report_endpoint, report_summary)
                                    gerofilter.store_pdf(report_id, report_id, report_pdf)

                                    gerofilter.check_duplicate(report_id)
                                    geronotify.notify(report_title, hunter_email, "NEW_REPORT")

                                    logging.getLogger("Gerologger").info('[CODE 201] Bug Hunter Report Saved Successfully')

                            # HUNTER CHECK STATUS
                            elif(code == 202): 
                                logging.getLogger("Gerologger").info('Report ID: ' + str(payload[0]))
                                report = BugReport.objects.get(report_id=payload[0])

                                payload[1] = report.report_title
                                payload[2] = report.report_status
                                payload[3] = gerocard.build_report_card(report)
                                logging.getLogger("Gerologger").info('[CODE 202] Bug Hunter Check Report Status')
                            
                            # HUNTER UPDATE/AMEND REPORT
                            elif(code == 203):
                                report_id = str(payload[0])
                                logging.getLogger("Gerologger").info('Report ID : ' + str(report_id))

                                update_summary, update_pdf, pdf_reason = read_submission(msg)
                                logging.getLogger("Gerologger").info('Update Summary : ' + str(update_summary) + '\n')

                                reason = gerofilter.pdf_reason_text(
                                    pdf_reason, gerofilter.attachment_size(msg))
                                if not reason and update_pdf is None and len(update_summary) <= 3:
                                    reason = gerofilter.REASON_EMPTY_UPDATE

                                if reason:
                                    payload[1] = BugReport.objects.get(report_id=report_id).report_title
                                    logging.getLogger("Gerologger").warning(
                                        '[ERROR 404] Update not valid: ' + reason)
                                    code = 404
                                    payload[3] = reason

                                else:
                                    with transaction.atomic():
                                        report = BugReport.objects.select_for_update().get(report_id=report_id)
                                        payload[1] = report.report_title

                                        if report.report_status > BOUNTY_CALC_STATUS:
                                            code = 408
                                            payload[2] = report.report_status
                                        elif not (report.report_permission & 4
                                                  or report.report_update_self < gerofilter.SELF_UPDATE_LIMIT):
                                            code = 407
                                        else:
                                            if report.report_permission & 4:
                                                report.report_permission -= 4
                                            else:
                                                report.report_update_self += 1
                                            report.report_update += 1
                                            update_id = report_id + "U" + str(report.report_update)
                                            report.save()
                                            logging.getLogger("Gerologger").info('Update ID : ' + str(update_id))

                                            stored = gerofilter.store_pdf(report_id, update_id, update_pdf)
                                            update_file_flag = 1 if stored else 0
                                            remaining = max(0, gerofilter.SELF_UPDATE_LIMIT - report.report_update_self)
                                            payload[3] = (
                                                f"You have {remaining} of {gerofilter.SELF_UPDATE_LIMIT} "
                                                "self-initiated updates left for this report. Once they are "
                                                "used up, further updates require a request from our team."
                                            )
                                            save_uan('U', update_id, report_id, email_date, update_summary, update_file_flag)

                                    if code == 203:
                                        geronotify.notify(report_id, hunter_email, "NEW_UPDATE")
                                        logging.getLogger("Gerologger").info(f'[CODE 203] Bug Hunter Update Saved Successfully (file={update_file_flag})')
                                    else:
                                        logging.getLogger("Gerologger").warning(
                                            f'[ERROR {code}] Update refused for {report_id} after locking the row')

                            # HUNTER APPEAL REPORT
                            elif(code == 204):
                                report_id = str(payload[0])
                                logging.getLogger("Gerologger").info('Report ID : ' + str(report_id))

                                appeal_summary, appeal_pdf, pdf_reason = read_submission(msg)
                                logging.getLogger("Gerologger").info('Appeal Summary : ' + str(appeal_summary) + '\n')

                                reason = gerofilter.pdf_reason_text(
                                    pdf_reason, gerofilter.attachment_size(msg))
                                if not reason and appeal_pdf is None and len(appeal_summary) <= 3:
                                    reason = gerofilter.REASON_EMPTY_APPEAL

                                if reason:
                                    payload[1] = BugReport.objects.get(report_id=report_id).report_title
                                    logging.getLogger("Gerologger").warning(
                                        '[ERROR 404] Appeal not valid: ' + reason)
                                    code = 404
                                    payload[3] = reason

                                else:
                                    with transaction.atomic():
                                        report = BugReport.objects.select_for_update().get(report_id=report_id)
                                        payload[1] = report.report_title

                                        if not report.report_permission & 2:
                                            code = 403
                                        elif report.report_appeal >= gerofilter.APPEAL_LIMIT:
                                            code = 409
                                        else:
                                            report.report_appeal += 1
                                            report.report_permission -= 2
                                            appeal_id = report_id + "A" + str(report.report_appeal)
                                            report.save()
                                            logging.getLogger("Gerologger").info('Appeal ID : ' + str(appeal_id))

                                            stored = gerofilter.store_pdf(report_id, appeal_id, appeal_pdf)
                                            appeal_file = 1 if stored else 0
                                            appeals_left = max(0, gerofilter.APPEAL_LIMIT - report.report_appeal)
                                            payload[3] = (
                                                f"You have {appeals_left} of {gerofilter.APPEAL_LIMIT} appeals "
                                                "left for this report. Once they are used up, our standing "
                                                "determination becomes final."
                                            )
                                            save_uan('A', appeal_id, report_id, email_date, appeal_summary, appeal_file)

                                    if code == 204:
                                        geronotify.notify(report_id, hunter_email, "NEW_APPEAL")
                                        logging.getLogger("Gerologger").info('[CODE 204] Bug Hunter Appeal Received Successfully')
                                    else:
                                        logging.getLogger("Gerologger").warning(
                                            f'[ERROR {code}] Appeal refused for {report_id} after locking the row')

                            # HUNTER AGREE
                            elif(code == 205):
                                report_id = str(payload[0])
                                logging.getLogger("Gerologger").info('Report ID: ' + str(report_id))

                                with transaction.atomic():
                                    report = BugReport.objects.select_for_update().get(report_id=report_id)
                                    payload[1] = report.report_title

                                    if (report.report_status != BOUNTY_CALC_STATUS
                                            or not report.report_permission & 2):
                                        code = 403
                                        payload[2] = report.report_status
                                    else:
                                        report.report_permission -= 2
                                        report.report_status += 1
                                        report.save()
                                        payload[2] = report.report_status

                                if code == 205:
                                    geronotify.notify(report_id, hunter_email, "NEW_AGREE")
                                    logging.getLogger("Gerologger").info('[CODE 205] Bug Hunter Agree Received Successfully')
                                else:
                                    logging.getLogger("Gerologger").warning(
                                        f'[ERROR {code}] Agree refused for {report_id}: '
                                        'the bounty decision is no longer open')

                            # HUNTER SUBMITTED NDA
                            elif(code == 206):
                                report_id = str(payload[0])
                                logging.getLogger("Gerologger").info('Report ID: ' + str(report_id))

                                nda_summary, nda_pdf, pdf_reason = read_submission(msg)
                                logging.getLogger("Gerologger").info('NDA Summary : ' + str(nda_summary) + '\n')

                                reason = gerofilter.pdf_reason_text(
                                    pdf_reason, gerofilter.attachment_size(msg))
                                if not reason and nda_pdf is None and len(nda_summary) <= 3:
                                    reason = gerofilter.REASON_EMPTY_UPDATE

                                if reason:
                                    payload[1] = BugReport.objects.get(report_id=report_id).report_title
                                    logging.getLogger("Gerologger").warning(
                                        '[ERROR 404] Data submission not valid: ' + reason)
                                    code = 404
                                    payload[3] = reason

                                else:
                                    with transaction.atomic():
                                        report = BugReport.objects.select_for_update().get(report_id=report_id)
                                        payload[1] = report.report_title

                                        if not report.report_permission & 1:
                                            code = 403
                                        else:
                                            report.report_nda += 1
                                            report.report_permission -= 1
                                            nda_id = report_id + "N" + str(report.report_nda)
                                            report.save()
                                            logging.getLogger("Gerologger").info('NDA ID : ' + str(nda_id))

                                            stored = gerofilter.store_pdf(report_id, nda_id, nda_pdf)
                                            nda_file_flag = 1 if stored else 0
                                            save_uan('N', nda_id, report_id, email_date, nda_summary, nda_file_flag)
                                            if not stored:
                                                code = 209

                                    if code in (206, 209):
                                        geronotify.notify(report_id, hunter_email, "NEW_NDA")
                                        logging.getLogger("Gerologger").info('[CODE 206] Bug Hunter NDA Received Successfully')
                                    else:
                                        logging.getLogger("Gerologger").warning(
                                            f'[ERROR {code}] Data submission refused for {report_id} after locking the row')

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

                            elif(code == 410):
                                payload[0] = ""
                                payload[3] = ""
                                logging.getLogger("Gerologger").info(
                                    f'[CODE 410] No reports on record for {hunter_email}')

                            # INVALID REPORT ID
                            elif(code == 405):
                                logging.getLogger("Gerologger").warning('[ERROR 405] Report ID not valid')

                            # USER NOT AUTHORIZED
                            elif(code == 403):
                                logging.getLogger("Gerologger").warning('[ERROR 403] User are not authorized!')

                            elif(code in (407, 408, 409)):
                                report = BugReport.objects.get(report_id=payload[0])
                                payload[1] = report.report_title
                                if code == 407:
                                    reason = "self-initiated update allowance exhausted, an amend request is needed"
                                elif code == 408:
                                    payload[2] = report.report_status
                                    reason = "the report has moved past Bounty Calculation"
                                else:
                                    reason = "appeal limit reached, the standing determination is final"
                                logging.getLogger("Gerologger").warning(
                                    f'[ERROR {code}] Hunter submission refused for {payload[0]}: {reason}')

                            # INVALID REPORT FORMAT
                            else:
                                logging.getLogger("Gerologger").warning(
                                    '[ERROR 404] Command not recognised in subject')
                                payload[3] = str(payload[0]).strip() or gerofilter.REASON_UNKNOWN_COMMAND
                                payload[0] = ""

                            logging.getLogger("Gerologger").info('============================')
                            geromailer.write_mail(code, payload, hunter_email,
                                                  in_reply_to=msg['Message-ID'])
                
                except Exception as e:
                    release_fingerprint(claimed)
                    logging.getLogger("Gerologger").error(f"Error processing email ID {i}: {str(e)}")
                    continue
                        
        else:
            logging.getLogger("Gerologger").debug(f'No new email in {folder_name}...')            

    except imaplib.IMAP4.abort as abort_err:
        logging.getLogger("Gerologger").info(f"IMAP connection aborted for {folder_name}, will reconnect")
        raise abort_err
    except Exception as e:
        logging.getLogger("Gerologger").error(f"Failed to read mail from {folder_name} = " + str(e) + "("  + str(ERROR_COUNT) + ")")
        ERROR_COUNT+=1
        raise e


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
        report.report_calc_sent_at = timezone.now()
        report.save()
        
    elif code == 703: # REQUEST NDA and OTHERS
        logging.getLogger("Gerologger").info('[CODE 703] Request NDA and Other Requirements to Bug Hunter')
        if not gerofilter.validate_permission("N", id):
            report.report_permission = report.report_permission + 1
            report.save()

    elif code == 705: # REQUEST PREREQUISITES ONLY (NO NDA)
        logging.getLogger("Gerologger").info('[CODE 705] Request Bounty Prerequisites (No NDA) to Bug Hunter')
        if not gerofilter.validate_permission("N", id):
            report.report_permission = report.report_permission + 1
            report.save()

    elif code == 704: # SEND CERTIFICATE and BOUNTY PROOF TO HUNTER
        # GET HUNTER NAME AND GENERATE CERTIFICATE
        hunter_email = report.hunter_email
        hunter = BugHunter.objects.get(hunter_email=hunter_email)

        try:
            gerocert.gerocert.generate(id, hunter.hunter_username, int(report.report_severity))

            # UPDATE HUNTER SCORE
            hunter.hunter_scores += int(report.report_severity)
            hunter.save()

            # UPDATE REPORT STATUS TO COMPLETE
            report.report_status += 1
            report.save()
            
            logging.getLogger("Gerologger").info('[CODE 704] Send Certificate and Bounty Proof to Bug Hunter')

        except Exception as e:
            logging.getLogger("Gerologger").error('[ERROR 704] Failed to Complete Report: '+str(e))

    payload = [id, report.report_title, report.report_status, note, report.report_severity]
    destination = report.hunter_email

    try:
        report.last_email_code = code
        report.last_email_note = note or ''
        report.save(update_fields=['last_email_code', 'last_email_note'])
    except Exception as e:
        logging.getLogger("Gerologger").warning(f"Could not record last email for {id}: {e}")

    geromailer.write_mail(code, payload, destination)

def check_mailbox_status():
    global MAILBOX_READY
        
    return MAILBOX_READY


def check_auto_agree():
    now = timezone.now()

    for candidate in BugReport.objects.filter(report_status=BOUNTY_CALC_STATUS):
        try:
            due = candidate.auto_accept_at
            if due is None or due > now:
                continue

            with transaction.atomic():
                report = BugReport.objects.select_for_update().get(report_id=candidate.report_id)
                due = report.auto_accept_at
                if due is None or due > now:
                    continue
                report.report_permission -= 2
                report.report_status += 1
                report.save()

            payload = [report.report_id, report.report_title, report.report_status,
                       "", report.report_severity]
            geromailer.write_mail(302, payload, report.hunter_email)
            geronotify.notify(report.report_id, report.hunter_email, "NEW_AGREE")
            logging.getLogger("Gerologger").info(
                f"[AUTO-AGREE] {report.report_id} advanced to Bounty in Process "
                f"({APPEAL_WINDOW_DAYS}d appeal window elapsed)")

        except Exception as e:
            logging.getLogger("Gerologger").error(
                f"Auto-agree check failed for {candidate.report_id}: {e}")

# RUN GEROMAIL MODULES
def run():
    global EMAIL, PWD, MAILBOX_READY, PARSER_RUNNING, IMAP_SERVER, IMAP_PORT

    if PARSER_RUNNING:
        logging.getLogger("Gerologger").warning("Geroparser already started.")
        return

    PARSER_RUNNING = True
    MAILBOX_READY = False
    mail = None

    try:
        while True:
            mailbox = MailBox.objects.get(mailbox_id=1)
            if mailbox.email and mailbox.password:
                break
            logging.getLogger("Gerologger").debug("Waiting for Mailbox Setup...")
            time.sleep(5)

        EMAIL       = mailbox.email
        PWD         = mailbox.password
        IMAP_SERVER = mailbox.mailbox_imap
        IMAP_PORT   = mailbox.mailbox_imap_port

        mail = imaplib.IMAP4_SSL(IMAP_SERVER, ssl_context=_get_ssl_context(), timeout=30)
        mail.login(EMAIL, PWD)
        MAILBOX_READY = True
        logging.getLogger("Gerologger").info("Geroparser connected to mailbox.")

        if mailbox.mailbox_status == 0:
            mailbox.mailbox_status = 1
            mailbox.save()

        folders_to_scan = ['inbox']
        spam_folder = get_spam_folder(mail)
        if spam_folder:
            folders_to_scan.append(spam_folder)

        session_start_time = time.time()
        loop_count = 0
        while PARSER_RUNNING:
            loop_count += 1
            if loop_count % 30 == 0:
                logging.getLogger("Gerologger").info(f"Geroparser Loop Count: {loop_count}")

            if time.time() - session_start_time > 10800:
                logging.getLogger("Gerologger").info("Session timeout (3 hours). Reconnecting...")
                return

            if not check_connection_alive(mail):
                logging.getLogger("Gerologger").info("Connection health check failed, reconnecting...")
                return

            try:
                for folder in folders_to_scan:
                    if folder != 'inbox' and (loop_count % 30 != 0):
                        continue
                    read_mail(mail, folder)
            except (imaplib.IMAP4.abort, OSError) as e:
                logging.getLogger("Gerologger").info(f"IMAP connection lost during poll, reconnecting: {e}")
                return

            check_auto_agree()

            if loop_count % 2880 == 0:
                try:
                    sweep_processed_mail()
                except Exception as e:
                    logging.getLogger("Gerologger").warning(
                        f"ProcessedMail sweep failed: {e}")

            try:
                connection.close()
            except Exception as e:
                logging.getLogger("Gerologger").debug(f"DB connection close warning: {e}")

            time.sleep(30)

    finally:
        MAILBOX_READY = False
        PARSER_RUNNING = False
        if mail:
            try:
                mail.logout()
            except Exception:
                pass

def missing_submission_files(report):
    targets = []
    report_id = report.report_id

    report_name = report_id + ".pdf"
    if not os.path.isfile(os.path.join(MEDIA_ROOT, report_id, report_name)):
        targets.append((report_id, None, None))

    rows = (
        ("U", BugReportUpdate.objects.filter(report_id=report_id, update_file=1),
         "update_id", "update_datetime"),
        ("A", BugReportAppeal.objects.filter(report_id=report_id, appeal_file=1),
         "appeal_id", "appeal_datetime"),
        ("N", BugReportNDA.objects.filter(report_id=report_id, nda_file=1),
         "nda_id", "nda_datetime"),
    )
    for kind, queryset, id_field, date_field in rows:
        for row in queryset:
            file_id = getattr(row, id_field)
            if not os.path.isfile(os.path.join(MEDIA_ROOT, report_id, file_id + ".pdf")):
                targets.append((file_id, kind, getattr(row, date_field)))

    return targets


# RECOVER LOSS FILES
def recover_loss_file_handler(BUGREPORTS):
    success = 0
    failed = 0
    logging.getLogger("Gerologger").info("Troubleshoot Started: RECOVER LOSS REPORT FILES")

    for report in BUGREPORTS:
        if report.report_status != 0: #EXCLUDE INVALID REPORTS
            for file_id, kind, when in missing_submission_files(report):
                logging.getLogger("Gerologger").info("Recovering = " + str(file_id) + ".pdf")
                if recover_loss_file(file_id, kind, when):
                    success += 1
                else:
                    failed += 1

    total = success + failed
    if total == 0 :
        logging.getLogger("Gerologger").info("NO LOSS REPORT FILES")
    else:
        success_rate = int(success / total * 100)
        logging.getLogger("Gerologger").info("RECOVERED " + str(success) + " / " + str(total) + " LOSS REPORT FILES")
        logging.getLogger("Gerologger").info("SUCCESS RATE: " +  str(success_rate) + "%")


def _closest_message_id(mail, id_list, when):
    if when is None or len(id_list) == 1:
        return int(id_list[-1])

    target = when.timestamp()
    best = int(id_list[-1])
    best_distance = None
    for raw_id in id_list:
        try:
            data = mail.fetch(str(int(raw_id)), '(BODY.PEEK[HEADER.FIELDS (DATE)])')
            for response_part in data[1] if isinstance(data, tuple) else data:
                part = response_part[1] if isinstance(response_part, tuple) else None
                if part is None:
                    continue
                candidate = parse_raw_message(part)
                distance = abs(message_timestamp(candidate) - target)
                if best_distance is None or distance < best_distance:
                    best_distance = distance
                    best = int(raw_id)
        except Exception as e:
            logging.getLogger("Gerologger").debug(f"Could not read the date of message {raw_id}: {e}")

    return best


def recover_loss_file(id, type, when=None):
    report_id = str(id[:12])
    recover = False

    # Ensure report folder exists before anything else
    fileDir = os.path.join(MEDIA_ROOT, report_id)
    os.makedirs(fileDir, exist_ok=True)

    report = BugReport.objects.get(report_id=report_id)
    hunter_email = str(report.hunter_email)
    report_title = str(report.report_title).replace('\r\n','')

    mailbox = MailBox.objects.get(mailbox_id=1)
    EMAIL       = normalize('NFKC', str(mailbox.email))
    PWD         = normalize('NFKC', str(mailbox.password))
    TYPE        = mailbox.mailbox_type
    IMAP_SERVER = normalize('NFKC', str(mailbox.mailbox_imap))
    IMAP_PORT   = mailbox.mailbox_imap_port

    try:
        # LOGIN TO IMAP / MAIL SERVER
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL,PWD)

        # READ DATA FROM INBOX
        mail.select('inbox')
        safe_email = _sanitize_imap_string(hunter_email)
        safe_title = _sanitize_imap_string(report_title)
        safe_id = _sanitize_imap_string(report_id)
        subjects = {
            None: ["SUBMIT_" + safe_title],
            "U": ["UPDATE_" + safe_id],
            "A": ["APPEAL_" + safe_id],
            "N": ["DATA_" + safe_id, "NDA_" + safe_id],
        }[type]

        id_list = []
        for subject in subjects:
            if TYPE == "1": # GMAIL
                SEARCH = "from:" + safe_email + " subject:" + subject
                data = mail.search(None, r'X-GM-RAW "'+SEARCH+'"')
            else:
                SEARCH = '(FROM "' + safe_email + '" SUBJECT "' + subject + '")'
                data = mail.search(None, SEARCH)

            mail_ids = data[1]
            id_list = mail_ids[0].split()
            if id_list:
                break

        # ITERATE THROUGH LIST OF EMAILS
        if(id_list):
            latest_email_id = _closest_message_id(mail, id_list, when)
            data = mail.fetch(str(latest_email_id), '(RFC822)' )

            for response_part in data:
                arr = response_part[0]

                # EMAIL EXISTS
                if isinstance(arr, tuple):
                    msg = parse_raw_message(arr[1])
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