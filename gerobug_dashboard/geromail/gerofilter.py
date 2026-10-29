import re
import os
import PyPDF2
import logging

from dashboards.models import (BOUNTY_CALC_STATUS, BugHunter, BugReport, BugReportUpdate,
                               BugReportAppeal, BugReportNDA)
from gerobug.settings import MEDIA_ROOT


MAX_PDF_BYTES = 25_000_000

FIELD_LIMITS = {
    "title": (3, 150),
    "type": (1, 100),
    "endpoint": (1, 255),
    "summary": (10, None),
}

REASON_PDF_TOO_LARGE = ("Your PDF is {mb:.1f} MB; the limit is 25 MB. "
                        "Put large evidence behind a link inside the PDF.")
REASON_PDF_INVALID = "The attachment is not a valid PDF file."
REASON_SUBMIT_NO_PDF = "Attach your report as a PDF file."
REASON_TITLE = "Title needs 3 to 150 characters."
REASON_TYPE = "TYPE is missing or longer than 100 characters."
REASON_ENDPOINT = "ENDPOINT is missing or longer than 255 characters."
REASON_SUMMARY = "SUMMARY needs at least 10 characters."
REASON_EMPTY_UPDATE = "Include a written description in the email body or attach a PDF."
REASON_EMPTY_APPEAL = "Include your reasoning in the email body or attach a PDF."
REASON_UNKNOWN_COMMAND = ("We could not recognise the command in the subject. "
                          "Send an email with the subject HELP for the list of commands.")



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

COMMENT_LIMIT = 10

COMMENT_STATUSES = (1, 2, 3, 4, 5, 6)

WITHDRAW_STATUSES = (1, 2)

REASON_EMPTY_COMMENT = "Write your question in the email body."

REASON_PDF_NOT_STORED_UPDATE = ("We could not store the attached PDF. "
                                "Please send it again in a new UPDATE.")
REASON_PDF_NOT_STORED_DATA = ("We could not store the attached PDF. "
                              "Please send it again in a new DATA email.")


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
    return str(report.hunter_email or '').strip().lower() == str(email or '').strip().lower()


_REPORT_ID_RE = re.compile(r'^[0-9A-Za-z]{12}$')


def valid_report_id(id):
    if not _REPORT_ID_RE.match(str(id or '')):
        return False
    return BugReport.objects.filter(report_id=id).exists()


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


def looks_like_pdf(part, data):
    if (part.get_content_type() or '').lower() == 'application/pdf':
        return True
    if str(part.get_filename() or '').lower().endswith('.pdf'):
        return True
    return bool(data) and data[:4] == b'%PDF'


def extract_pdf_sized(msg):
    reason = "none"
    reason_size = 0

    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue
        if not part.get_filename():
            continue

        data = part.get_payload(decode=True)
        if not data:
            continue
        if not looks_like_pdf(part, data):
            continue

        size = len(data)
        logging.getLogger("Gerologger").info('File size = ' + str(size))

        if size > MAX_PDF_BYTES:
            if reason in ("none", "not_pdf"):
                reason, reason_size = "too_large", size
            continue
        if not check_pdf(data):
            logging.getLogger("Gerologger").warning(
                'Invalid PDF detected in memory, file not written to disk')
            if reason == "none":
                reason, reason_size = "not_pdf", size
            continue
        return data, "", size

    return None, reason, reason_size


def extract_pdf(msg):
    data, reason, _size = extract_pdf_sized(msg)
    return data, reason


def pdf_reason_text(reason, size=0):
    if reason == "too_large":
        return REASON_PDF_TOO_LARGE.format(mb=size / 1000000.0)
    if reason == "not_pdf":
        return REASON_PDF_INVALID
    return ""


def store_pdf(report_id, file_id, data, base=None):
    if base is None:
        base = MEDIA_ROOT
    if not data:
        return False

    file_dir = os.path.join(base, report_id)
    file_path = os.path.join(file_dir, file_id + '.pdf')

    real_filepath = os.path.realpath(file_path)
    real_basepath = os.path.realpath(base)
    if not real_filepath.startswith(real_basepath + os.sep):
        logging.getLogger("Gerologger").error(
            f"Path traversal blocked: {file_path} resolves outside {base}")
        return False

    if os.path.isfile(file_path):
        logging.getLogger("Gerologger").warning(
            f"Refusing to overwrite an existing file: {file_path}")
        return False

    os.makedirs(file_dir, exist_ok=True)
    with open(file_path, 'wb') as fp:
        fp.write(data)
    return True


def validate_submit_fields(title, atk_type, endpoint, summary):
    title = (title or '').strip()
    atk_type = (atk_type or '').strip()
    endpoint = (endpoint or '').strip()
    summary = (summary or '').strip()

    low, high = FIELD_LIMITS["title"]
    if len(title) < low or len(title) > high:
        return REASON_TITLE
    low, high = FIELD_LIMITS["type"]
    if len(atk_type) < low or len(atk_type) > high:
        return REASON_TYPE
    low, high = FIELD_LIMITS["endpoint"]
    if len(endpoint) < low or len(endpoint) > high:
        return REASON_ENDPOINT
    low, high = FIELD_LIMITS["summary"]
    if len(summary) < low:
        return REASON_SUMMARY
    return ""


def validate_attachment(msg, id, FILEPATH=None):
    data, reason = extract_pdf(msg)
    if reason:
        return False
    return store_pdf(str(id)[:12], str(id), data,
                     base=FILEPATH if FILEPATH is not None else MEDIA_ROOT)


_FIELD_LINE_RE = re.compile(
    r'^\*{0,2}[ \t]*+(TYPE|ENDPOINT|SUMMARY)[ \t]*+\*{0,2}[ \t]*+[=:-][ \t]*+(.*)$', re.IGNORECASE)


# PARSE EMAIL BODY
def parse_body(body):
    fields = {'TYPE': [], 'ENDPOINT': [], 'SUMMARY': []}
    current = None

    try:
        for line in str(body or '').replace('\r\n', '\n').split('\n'):
            line = line[:10000].strip()
            match = _FIELD_LINE_RE.match(line)
            if match:
                current = match.group(1).upper()
                fields[current].append(match.group(2).strip())
            elif current == 'SUMMARY':
                fields['SUMMARY'].append(line.strip())
            elif current:
                fields[current].append(line.strip())

        atk_type = ' '.join(part for part in fields['TYPE'] if part).strip()
        endpoint = ' '.join(part for part in fields['ENDPOINT'] if part).strip()
        endpoint = re.sub(r'<[^>]*>', '', endpoint).strip()
        summary = '\n'.join(fields['SUMMARY']).strip()

    except Exception as e:
        logging.getLogger("Gerologger").error(str(e))
        return '', '', ''

    return atk_type, endpoint, summary


_SUBJECT_MAX = 500

_REPLY_PREFIX = re.compile(
    r'^(?:\s*(?:(?:re|fw|fwd|aw|sv|wg|tr|rif)\s?(?:\[\d+\])?\s?:|\[[^\]]{1,40}\]))+\s*',
    re.I)
_COMMAND = re.compile(
    r'^(SUBMIT|CHECK|UPDATE|APPEAL|AGREE|DATA|NDA|COMMENT|WITHDRAW)\s*[_:\- ]\s*(.*)$'
    r'|^(STATUS_OVERVIEW|MY_SCORE|HELP|COMMANDS)\b', re.I)
_REPORT_ID = re.compile(r'^([0-9A-Za-z]{12})(?![0-9A-Za-z])')

_REST_MAX = 64


def parse_subject(subject):
    s = str(subject or '')[:_SUBJECT_MAX]
    s = _REPLY_PREFIX.sub('', s).strip()
    m = _COMMAND.match(s)
    if not m:
        return None, ''
    if m.group(3):
        return m.group(3).upper(), ''
    verb, rest = m.group(1).upper(), m.group(2).strip()
    if verb == 'SUBMIT':
        return verb, rest
    idm = _REPORT_ID.match(rest) or _REPORT_ID.match(rest.replace(' ', ''))
    return verb, (idm.group(1).upper() if idm else rest[:_REST_MAX])


_SUBJECT_ACTIONS = {
    'CHECK':  (202, None),
    'UPDATE': (203, 'U'),
    'APPEAL': (204, 'A'),
    'AGREE':  (205, 'A'),
    'DATA':   (206, 'N'),
    'NDA':    (206, 'N'),
}


def classify_action(email, subject):
    try:
        verb, rest = parse_subject(subject)

        if verb == 'SUBMIT':
            return 201, rest

        if verb in _SUBJECT_ACTIONS:
            code, permission = _SUBJECT_ACTIONS[verb]
            id = rest
            if not valid_report_id(id):
                return 405, id
            if not validate_user(email, id):
                return 403, id
            if code == 203:
                if not validate_update_stage(id):
                    return 408, id
                if not validate_permission('U', id) and not validate_self_update(id):
                    return 407, id
            elif permission and not validate_permission(permission, id):
                return 403, id
            if code == 204 and not validate_appeal(id):
                return 409, id
            return code, id

        if verb == 'MY_SCORE':
            hunter = BugHunter.objects.filter(hunter_email__iexact=email).first()
            if hunter is not None:
                return 207, str(hunter.hunter_scores)
            if BugReport.objects.filter(hunter_email__iexact=email).exists():
                return 207, "0"
            return 410, " "

        if verb == 'STATUS_OVERVIEW':
            if BugReport.objects.filter(hunter_email__iexact=email).exists():
                from . import gerocard
                return 208, gerocard.build_overview_rows(email)
            else:
                return 410, " "

        if verb == 'COMMENT':
            id = rest
            if not valid_report_id(id):
                return 405, id
            if not validate_user(email, id):
                return 403, id
            report = BugReport.objects.get(report_id=id)
            if report.report_status not in COMMENT_STATUSES:
                return 413, id
            if report.report_hunter_comment >= COMMENT_LIMIT:
                return 411, id
            return 211, id

        if verb == 'WITHDRAW':
            id = rest
            if not valid_report_id(id):
                return 405, id
            if not validate_user(email, id):
                return 403, id
            report = BugReport.objects.get(report_id=id)
            if report.report_status not in WITHDRAW_STATUSES:
                return 412, id
            return 212, id

        if verb in ('HELP', 'COMMANDS'):
            from . import gerocard
            return 210, gerocard.build_help(email)

        return 404, REASON_UNKNOWN_COMMAND

    except Exception as e:
        logging.getLogger("Gerologger").error(str(e))
        return 404, " "