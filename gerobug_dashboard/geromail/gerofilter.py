import re
import os
import html
import PyPDF2
import logging

from django.db import transaction

from dashboards.models import (BOUNTY_CALC_STATUS, BugHunter, BugReport, BugReportUpdate,
                               BugReportAppeal, BugReportNDA, ReportStatus)



def normalize_endpoint(value):
    text = (value or "").strip().lower()
    for prefix in ("https://", "http://"):
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    if text.startswith("www."):
        text = text[4:]
    for separator in ("#", "?"):
        text = text.split(separator, 1)[0]
    return text.rstrip("/")


def normalize_attack(value):
    return " ".join((value or "").split()).casefold()


# CHECK IF POSSIBLE DUPLICATE (ADVISORY BADGE ON THE LATER REPORT)
def check_duplicate(id):
    report = BugReport.objects.get(report_id=id)
    attack = normalize_attack(report.report_attack)
    endpoint = normalize_endpoint(report.report_endpoint)
    if not endpoint:
        return

    matches = [
        other
        for other in BugReport.objects.exclude(report_id=id).only(
            "report_id", "report_endpoint", "report_attack",
            "report_datetime", "report_duplicate",
        )
        if normalize_endpoint(other.report_endpoint) == endpoint
        and normalize_attack(other.report_attack) == attack
    ]
    if not matches:
        return

    logger = logging.getLogger("Gerologger")
    when = report.report_datetime
    earlier = [m for m in matches if m.report_datetime and when and m.report_datetime < when]
    if earlier or not when:
        report.report_duplicate = 1
        originals = sorted(earlier or matches, key=lambda m: (m.report_datetime is None, m.report_datetime))
        report.report_duplicate_of = originals[0].report_id
        report.save(update_fields=["report_duplicate", "report_duplicate_of"])
        logger.warning(
            f"Possible Duplicate Report: {id} matches "
            f"{', '.join(m.report_id for m in (earlier or matches))} on {endpoint}"
        )
        return

    for later in matches:
        if later.report_duplicate:
            continue
        later.report_duplicate = 1
        later.report_duplicate_of = id
        later.save(update_fields=["report_duplicate", "report_duplicate_of"])
        logger.warning(
            f"Possible Duplicate Report: {later.report_id} matches earlier report {id} "
            f"on {endpoint}"
        )

APPEAL_LIMIT = 3


# VALIDATE APPEAL LIMIT
def validate_appeal(id):
    report = BugReport.objects.get(report_id=id)
    return report.report_appeal < APPEAL_LIMIT


SELF_UPDATE_LIMIT = 3


def validate_update_stage(id):
    report = BugReport.objects.get(report_id=id)
    return report.report_status <= BOUNTY_CALC_STATUS


def validate_self_update(id):
    report = BugReport.objects.get(report_id=id)
    return report.report_update_self < SELF_UPDATE_LIMIT


def consume_update_allowance(id):
    with transaction.atomic():
        report = BugReport.objects.select_for_update().get(report_id=id)
        if report.report_permission >= 4:
            report.report_permission -= 4
        else:
            report.report_update_self += 1
        report.save()
        return max(0, SELF_UPDATE_LIMIT - report.report_update_self)


# VALIDATE IF CERTAIN OPERATION IS PERMITTED
def validate_permission(operation, id):
    report = BugReport.objects.get(report_id=id)
    permission = report.report_permission
    permited = []

    if permission <= 0: # NO PERMISSION
        logging.getLogger("Gerologger").info("No Permission")
        return False
    else:
        if permission >= 4: # UPDATE
            permission = permission - 4
            if report.report_update < 99:
                permited.append("U")

        if permission >= 2: # APPEAL
            permission = permission - 2
            if report.report_appeal < 99:
                permited.append("A")

        if permission >= 1: # NDA
            permission = permission - 1
            if report.report_nda < 99:
                permited.append("N")

        logging.getLogger("Gerologger").info("Permission = " + str(report.report_permission) + " " + str(permited))
        if operation in permited:
            logging.getLogger("Gerologger").info(str(operation) + " is Permitted")
            return True
        else:
            logging.getLogger("Gerologger").info(str(operation) + " is NOT Permitted")
            return False


# VALIDATE USER OWNERSHIP FOR REPORT ID
def validate_user(email, id):
    report = BugReport.objects.get(report_id=id)
    
    if(report.hunter_email == email):
        return True
    else:    
        return False


# VALIDATE REPORT ID
def validate_id(id):
    if(len(id) == 12) & (id.isalnum()):
        if BugReport.objects.filter(report_id=id).exists():
            return True
        else:    
            return False
    elif(len(id) > 12) & (id.isalnum()):
        if BugReportUpdate.objects.filter(update_id=id).exists():
            return True
        elif BugReportAppeal.objects.filter(appeal_id=id).exists():
            return True
        elif BugReportNDA.objects.filter(nda_id=id).exists():
            return True
        else:    
            return False
    else:    
        return False


# VALIDATE PDF FILE
def check_pdf(file):
    try:
        if isinstance(file, bytes):
            import io
            PyPDF2.PdfFileReader(io.BytesIO(file))
        else:
            PyPDF2.PdfFileReader(open(file, "rb"))
    except Exception as e:
        logging.getLogger("Gerologger").error(str(e))
        logging.getLogger("Gerologger").error("Invalid PDF File")
        return False
    else:
        return True


# VALIDATE AND DOWNLOAD ATTACHMENT
def validate_attachment(msg, id, FILEPATH):
    valid = False
    filePath = ''
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue

        if part.get('Content-Disposition') is None:
            continue
        
        fileName = part.get_filename()
        if bool(fileName):
            report_id = id[:12]
            fileName = id + '.pdf'
            fileDir = os.path.join(FILEPATH, report_id)
            filePath = os.path.join(fileDir, fileName)

            real_filepath = os.path.realpath(filePath)
            real_basepath = os.path.realpath(FILEPATH)
            if not real_filepath.startswith(real_basepath + os.sep):
                logging.getLogger("Gerologger").error(f"Path traversal blocked: {filePath} resolves outside {FILEPATH}")
                break

            file = part.get_payload(decode=True)
            fileSize = len(file)
            logging.getLogger("Gerologger").info('File size = ' + str(fileSize))

            if fileSize >= 25000000:
                pass
            elif not os.path.isfile(filePath):
                if not check_pdf(file):
                    logging.getLogger("Gerologger").warning('Invalid PDF detected in memory, file not written to disk')
                    continue

                if not os.path.exists(fileDir):
                    os.mkdir(fileDir)

                fp = open(filePath, 'wb')
                fp.write(file)
                fp.close()
                valid = True

                break
    
    return valid


# PARSE EMAIL BODY
def parse_body(body):
    endpoint = '' 
    summary = ''

    try:
        type = re.search('(TYPE=|TYPE =|TYPE)((.|\n)*)(ENDPOINT=|ENDPOINT =|ENDPOINT)', body.replace('*', ''))
        if type != None:
            type = type.group(2)
            type = str(type.replace("\n",""))
        else:
            type = ''

        endpoint = re.search('(ENDPOINT=|ENDPOINT =|ENDPOINT)((.|\n)*)(SUMMARY=|SUMMARY =|SUMMARY)', body.replace('*', ''))
        if endpoint != None:
            endpoint = endpoint.group(2)
            endpoint = re.sub(r"<.*>", "", str(endpoint))
            endpoint = str(endpoint.replace("\n",""))
        else:
            endpoint = ''

        summary = re.search('(SUMMARY=|SUMMARY =|SUMMARY)(.*)', body.replace('\n', ' ').replace('*', ''))
        if summary != None:
            summary = summary.group(2)
        else:
            summary = ''

    except Exception as e:
        logging.getLogger("Gerologger").error(str(e))

    return type, endpoint, summary


# CLASSIFY ACTION BY EMAIL SUBJECT
def classify_action(email, subject):
    try:
        if(re.search(r'^SUBMIT_', subject)):
            title = subject[7 : ]
            return 201, title

        elif(re.search(r'^CHECK_', subject)):
            id = subject[6 : ]
            id = id.replace(' ','')
            if validate_id(id):
                if validate_user(email, id):
                    return 202, id
                else:
                    return 403, id
            else:
                return 405, id

        elif(re.search(r'^UPDATE_', subject)):
            id = subject[7 : ]
            id = id.replace(' ','')
            if validate_id(id):
                if validate_user(email, id):
                    if not validate_update_stage(id):
                        return 408, id
                    if validate_permission("U", id) or validate_self_update(id):
                        return 203, id
                    else:
                        return 407, id
                else:
                    return 403, id
            else:
                return 405, id

        elif(re.search(r'^APPEAL_', subject)):
            id = subject[7 : ]
            id = id.replace(' ','')
            if validate_id(id):
                if validate_user(email, id):
                    if validate_permission("A", id):
                        if validate_appeal(id):
                            return 204, id
                        else:
                            return 409, id
                    else:
                        return 403, id
                else:
                    return 403, id
            else:
                return 405, id

        elif(re.search(r'^AGREE_', subject)):
            id = subject[6 : ]
            id = id.replace(" ","")
            if validate_id(id):
                if validate_user(email, id):
                    if validate_permission("A", id):
                        return 205, id
                    else:
                        return 403, id
                else:
                    return 403, id
            else:
                return 405, id

        elif(re.search(r'^NDA_', subject)):
            id = subject[4 : ]
            if validate_id(id):
                if validate_user(email, id):
                    if validate_permission("N", id):
                        return 206, id
                    else:
                        return 403, id
                else:
                    return 403, id
            else:
                return 405, id

        elif(re.search(r'^DATA_', subject)):
            id = subject[5 : ]
            if validate_id(id):
                if validate_user(email, id):
                    if validate_permission("N", id):
                        return 206, id
                    else:
                        return 403, id
                else:
                    return 403, id
            else:
                return 405, id

        elif(re.search(r'^MY_SCORE$', subject)):
            if BugHunter.objects.filter(hunter_email=email).exists():
                hunter = BugHunter.objects.get(hunter_email=email)
                return 207, str(hunter.hunter_scores)
            else:
                return 403, " "
        
        elif(re.search(r'^STATUS_OVERVIEW$', subject)):
            if BugHunter.objects.filter(hunter_email=email).exists():
                if BugReport.objects.filter(hunter_email=email).exists():
                    reports = []
                    for report in BugReport.objects.filter(hunter_email=email):
                        status = ReportStatus.objects.get(status_id=report.report_status)
                        status = status.status_name
                        cell = "padding:10px 12px; border:1px solid #d2d6dc; vertical-align:top;"
                        x = (
                            "<tr>"
                            "<td style=\"" + cell + " font-family:'Courier New', monospace; white-space:nowrap;\">" + html.escape(report.report_id) + "</td>"
                            "<td style=\"" + cell + "\">" + html.escape(report.report_title) + "</td>"
                            "<td style=\"" + cell + "\">" + html.escape(status) + "</td>"
                            "</tr>"
                        )
                        reports.append(x)
                    
                    return 208, reports
                else:
                    return 403, " "
            else:
                return 403, " "
            
        else:
            return 404, " "

    except Exception as e:
        logging.getLogger("Gerologger").error(str(e))