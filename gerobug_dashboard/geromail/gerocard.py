import html
import urllib.parse

from dashboards.models import (APPEAL_WINDOW_DAYS, BOUNTY_CALC_STATUS, BugReport,
                               BugReportAppeal, BugReportHunterComment, BugReportNDA,
                               BugReportUpdate, ReportStatus)
from prerequisites.models import MailBox

from . import gerofilter

TR_OPEN = "<tr>"
TD_CLOSE = "</td>"


STAGE_TEXT = {
    0: "This report was closed and will not be processed further.",
    1: "We received your report and it is waiting for a triager.",
    2: "A triager is reviewing your report and may ask you for more information.",
    3: "The issue is confirmed and is being fixed. We may ask you to retest.",
    4: "A fix is in place and is being retested.",
    5: "We sent you a bounty decision. Agree or appeal before the deadline.",
    6: "You agreed to the decision. We may ask for documents before payment.",
    7: "This report is complete. Thank you for your contribution.",
}

STAGE_COUNT = 7

VERB_LABELS = {
    "SUBMIT": "Send a new report",
    "STATUS_OVERVIEW": "List my reports",
    "MY_SCORE": "Check my score",
    "HELP": "Send me this list again",
    "COMMENT": "Ask a question",
    "WITHDRAW": "Withdraw this report",
    "UPDATE": "Send update",
    "APPEAL": "Appeal the decision",
    "AGREE": "Agree to the decision",
    "DATA": "Send the requested data",
    "CHECK": "Check this report",
}

LAST_EMAIL_LABELS = {
    212: "You withdrew your report",
    300: "We closed your report",
    301: "We changed the stage of your report",
    701: "We asked you for more information",
    702: "We sent you the bounty decision",
    703: "We asked for bounty prerequisites and a signed NDA",
    704: "We completed your report and sent your certificate",
    705: "We asked for bounty prerequisites",
}

COMMAND_HELP = (
    ("SUBMIT", "SUBMIT_Your report title",
     "Send a new report. Put TYPE, ENDPOINT and SUMMARY in the body and "
     "attach the full report as a PDF."),
    ("CHECK", "CHECK_Report ID",
     "Get the full status card for one report."),
    ("STATUS_OVERVIEW", "STATUS_OVERVIEW",
     "List every report you have sent us and what each one needs."),
    ("MY_SCORE", "MY_SCORE",
     "See the score you have earned in this program."),
    ("HELP", "HELP",
     "Send this list of commands back to you."),
    ("UPDATE", "UPDATE_Report ID",
     "Add new information to a report, with text or a PDF."),
    ("COMMENT", "COMMENT_Report ID",
     "Ask our team a question about a report while it is open. Text only."),
    ("DATA", "DATA_Report ID",
     "Send the documents we asked for before a payout."),
    ("AGREE", "AGREE_Report ID",
     "Accept our bounty decision for a report."),
    ("APPEAL", "APPEAL_Report ID",
     "Tell us why you think the bounty decision should change."),
    ("WITHDRAW", "WITHDRAW_Report ID",
     "Withdraw a report while it is still in review."),
)

HELP_VERBS_WITHOUT_ID = ("SUBMIT", "STATUS_OVERVIEW", "MY_SCORE", "HELP")

OPEN_STATUSES = (1, 2, 3, 4, 5, 6)

ACTION_LABELS = {
    "update": "Send us more information",
    "decision": "Agree or appeal the bounty decision",
    "data": "Send the requested documents",
    "closed": "Nothing to do, this report is closed",
    "completed": "Nothing to do, this report is complete",
    "none": "Nothing needed from you right now",
}

_H = "margin:0 0 8px 0; font-size:15px; font-weight:bold;"
_P = "margin:0 0 10px 0;"
_BOX = ("margin:0 0 20px 0; padding:14px 16px; background-color:#f0f4f8; "
        "border-left:4px solid #1f2933; border-radius:4px;")
_LIST = "margin:0 0 10px 0; padding-left:22px;"
_MONO = "font-family:'Courier New', monospace;"
_BTN = ("display:inline-block; margin:0 8px 8px 0; padding:10px 18px; "
        "background-color:#1f2933; color:#ffffff; text-decoration:none; "
        "border-radius:4px; font-weight:bold;")
_TABLE = ("width:100%; border-collapse:collapse; margin:0 0 20px 0; "
          "font-size:14px;")
_TH = ("padding:8px 12px; background-color:#1f2933; color:#ffffff; "
       "border:1px solid #1f2933;")
_TD = "padding:8px 12px; border:1px solid #d2d6dc; vertical-align:top;"
_LINK = "color:#1f6feb;"


def _esc(value):
    return html.escape(str(value if value is not None else ""))


def _date(value):
    if not value:
        return ""
    try:
        return value.strftime("%d %b %Y").lstrip("0")
    except Exception:
        return ""


def _para(text, style=_P):
    return '<p style="' + style + '">' + text + "</p>"


def _heading(text):
    return '<p style="' + _H + '">' + text + "</p>"


def _status_name(status):
    try:
        row = ReportStatus.objects.filter(status_id=status).first()
    except Exception:
        row = None
    if row is not None:
        return row.status_name
    return str(status)


def mailbox_address():
    try:
        mailbox = MailBox.objects.filter(mailbox_id=1).first()
    except Exception:
        return ""
    if mailbox is None or not mailbox.email or "@" not in mailbox.email:
        return ""
    return mailbox.email


def mailto(verb, report_id=None):
    address = mailbox_address()
    if not address:
        return ""
    subject = str(verb or "").upper()
    if report_id:
        subject = subject + "_" + str(report_id)
    elif subject == "SUBMIT":
        subject = subject + "_"
    return ("mailto:" + urllib.parse.quote(address, safe="@")
            + "?subject=" + urllib.parse.quote(subject, safe=""))


def render_actions(report_id, verbs):
    buttons = []
    for verb in verbs:
        verb = str(verb or "").upper()
        link = mailto(verb, report_id)
        if not link:
            continue
        label = VERB_LABELS.get(verb, verb.title())
        buttons.append('<a href="' + _esc(link) + '" style="' + _BTN + '">'
                       + _esc(label) + "</a>")
    if not buttons:
        return ""
    return '<p style="' + _P + '">' + "".join(buttons) + "</p>"


def action_needed(report):
    permission = max(int(report.report_permission or 0), 0)
    status = int(report.report_status or 0)

    if status == 0:
        return "closed", ACTION_LABELS["closed"]
    if status == 7:
        return "completed", ACTION_LABELS["completed"]
    if status == BOUNTY_CALC_STATUS and permission & 2:
        return "decision", ACTION_LABELS["decision"]
    if permission & 4:
        return "update", ACTION_LABELS["update"]
    if permission & 1:
        return "data", ACTION_LABELS["data"]
    return "none", ACTION_LABELS["none"]


CLOSED_ALLOWANCE_LINE = "This report is closed, so nothing further can be sent."


def allowance_lines(report):
    lines = []
    updates_left = max(0, gerofilter.SELF_UPDATE_LIMIT - int(report.report_update_self or 0))
    appeals_left = max(0, gerofilter.APPEAL_LIMIT - int(report.report_appeal or 0))
    status = int(report.report_status or 0)

    if status in (0, 7):
        return [CLOSED_ALLOWANCE_LINE]

    if status > BOUNTY_CALC_STATUS:
        lines.append("Updates are closed for this report, the finding is settled.")
    else:
        lines.append(
            "Updates you can send on your own initiative: "
            + str(updates_left) + " of " + str(gerofilter.SELF_UPDATE_LIMIT)
            + ". An update we ask for does not count.")
    lines.append("Appeals left: " + str(appeals_left) + " of "
                 + str(gerofilter.APPEAL_LIMIT) + ".")
    comments_left = max(0, gerofilter.COMMENT_LIMIT - int(report.report_hunter_comment or 0))
    lines.append("Questions you can still ask about this report: "
                 + str(comments_left) + " of " + str(gerofilter.COMMENT_LIMIT)
                 + ". A question does not use an update.")
    return lines


def _submission_rows(report):
    rows = [("Original report", report.report_datetime, True)]

    for update in BugReportUpdate.objects.filter(report_id=report.report_id).order_by("update_datetime", "update_id"):
        rows.append((update.update_id, update.update_datetime, bool(update.update_file)))
    for appeal in BugReportAppeal.objects.filter(report_id=report.report_id).order_by("appeal_datetime", "appeal_id"):
        rows.append((appeal.appeal_id, appeal.appeal_datetime, bool(appeal.appeal_file)))
    for nda in BugReportNDA.objects.filter(report_id=report.report_id).order_by("nda_datetime", "nda_id"):
        rows.append((nda.nda_id, nda.nda_datetime, bool(nda.nda_file)))
    for comment in BugReportHunterComment.objects.filter(report_id=report.report_id).order_by("comment_datetime", "comment_id"):
        rows.append((comment.comment_id, comment.comment_datetime, False))

    head, tail = rows[0], rows[1:]
    tail.sort(key=lambda row: (row[1] is None, row[1]))
    return [head] + tail


def _action_section(report):
    key, label = action_needed(report)
    report_id = report.report_id
    body = [_heading("What we need from you")]

    if key == "update":
        body.append(_para("We asked you for more information before we can carry on."))
        if int(report.last_email_code or 0) == 701 and report.last_email_note:
            body.append(_para("What we asked for: " + _esc(report.last_email_note)))
        body.append(render_actions(report_id, ["UPDATE"]))
    elif key == "decision":
        body.append(_para("We sent you our bounty decision for this report."))
        body.append(_para("Severity: <b>" + _esc(report.severity_label) + "</b> (score "
                          + _esc(report.report_severity) + " out of 10)"))
        due = _date(report.auto_accept_at)
        if due:
            body.append(_para("Reply AGREE or APPEAL by " + _esc(due)
                              + ". After that date the decision counts as agreed."))
        else:
            body.append(_para("Reply AGREE or APPEAL within " + str(APPEAL_WINDOW_DAYS)
                              + " days. After that the decision counts as agreed."))
        body.append(render_actions(report_id, ["AGREE", "APPEAL"]))
    elif key == "data":
        nda = int(report.last_email_code or 0) == 703
        body.append(_para("We asked for the prerequisites we need before the payout."
                          + (" A signed NDA is required." if nda else "")))
        if report.last_email_note:
            body.append(_para("What we asked for: " + _esc(report.last_email_note)))
        body.append(render_actions(report_id, ["DATA"]))
    elif key == "closed":
        body.append(_para("This report was closed as not valid for the program."))
        if int(report.last_email_code or 0) in (300, 212) and report.last_email_note:
            body.append(_para("Reason we gave: " + _esc(report.last_email_note)))
    elif key == "completed":
        body.append(_para("This report is complete and your certificate was emailed to you."))
    else:
        body.append(_para("Nothing is needed from you right now. We will email you when "
                          "the next step is ready."))

    return '<div style="' + _BOX + '">' + "".join(part for part in body if part) + "</div>"


def build_report_card(report):
    status = int(report.report_status or 0)
    parts = []

    parts.append(_heading("Report " + _esc(report.report_id)))
    parts.append(_para("<b>" + _esc(report.report_title) + "</b>"))
    stage_line = ("Stage " + str(status) + " of " + str(STAGE_COUNT) + ": <b>"
                  + _esc(_status_name(status)) + "</b>")
    since = _date(report.report_status_changed_at)
    if since:
        stage_line = stage_line + ", since " + _esc(since)
    parts.append(_para(stage_line))

    parts.append(_action_section(report))

    parts.append(_heading("Your allowances"))
    parts.append('<ul style="' + _LIST + '">'
                 + "".join("<li>" + _esc(line) + "</li>" for line in allowance_lines(report))
                 + "</ul>")

    parts.append(_heading("What this stage means"))
    parts.append(_para(_esc(STAGE_TEXT.get(status, STAGE_TEXT[1]))))

    parts.append(_heading("Your submissions"))
    rows = []
    for name, when, has_pdf in _submission_rows(report):
        rows.append(
            TR_OPEN
            + '<td style="' + _TD + " " + _MONO + ' white-space:nowrap;">' + _esc(name) + TD_CLOSE
            + '<td style="' + _TD + ' white-space:nowrap;">' + _esc(_date(when) or "-") + TD_CLOSE
            + '<td style="' + _TD + '">' + ("yes" if has_pdf else "no") + TD_CLOSE
            + "</tr>")
    parts.append(
        '<table role="presentation" cellpadding="0" cellspacing="0" style="' + _TABLE + '">'
        "<thead><tr>"
        '<th align="left" style="' + _TH + '">Submission</th>'
        '<th align="left" style="' + _TH + '">Date</th>'
        '<th align="left" style="' + _TH + '">PDF</th>'
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>")

    label = LAST_EMAIL_LABELS.get(int(report.last_email_code or 0))
    if label:
        parts.append(_heading("Last message from us"))
        parts.append(_para(_esc(label)))
        if report.last_email_note:
            parts.append(_para(_esc(report.last_email_note)))

    parts.append(_heading("Your original submission"))
    parts.append(
        '<table role="presentation" cellpadding="0" cellspacing="0" style="' + _TABLE + '">'
        "<tbody>"
        '<tr><td style="' + _TD + '">Submitted</td><td style="' + _TD + '">'
        + _esc(_date(report.report_datetime) or "-") + "</td></tr>"
        '<tr><td style="' + _TD + '">Attack type</td><td style="' + _TD + '">'
        + _esc(report.report_attack) + "</td></tr>"
        '<tr><td style="' + _TD + '">Endpoint</td><td style="' + _TD + '">'
        + _esc(report.report_endpoint) + "</td></tr>"
        "</tbody></table>")

    return "".join(parts)


def build_overview_rows(email):
    reports = list(BugReport.objects.filter(hunter_email__iexact=email))
    ordered = []
    for report in reports:
        key, label = action_needed(report)
        needs = key in ("update", "decision", "data")
        ordered.append((0 if needs else 1, report, key, label, needs))
    ordered.sort(key=lambda item: (item[0], item[1].report_datetime is None,
                                   -(item[1].report_datetime.timestamp()
                                     if item[1].report_datetime else 0)))

    rows = []
    for _, report, _key, label, needs in ordered:
        link = mailto("CHECK", report.report_id)
        if link:
            id_cell = ('<a href="' + _esc(link) + '" style="' + _LINK + '">'
                       + _esc(report.report_id) + "</a>")
        else:
            id_cell = _esc(report.report_id)
        needs_cell = _esc(label) if needs else "-"
        rows.append(
            TR_OPEN
            + '<td style="' + _TD + " " + _MONO + ' white-space:nowrap;">' + id_cell + TD_CLOSE
            + '<td style="' + _TD + '">' + _esc(report.report_title) + TD_CLOSE
            + '<td style="' + _TD + '">' + _esc(_status_name(report.report_status)) + TD_CLOSE
            + '<td style="' + _TD + '">' + needs_cell + TD_CLOSE
            + "</tr>")
    return rows


def _help_command_rows():
    rows = []
    for _verb, subject, description in COMMAND_HELP:
        rows.append(
            TR_OPEN
            + '<td style="' + _TD + " " + _MONO + ' white-space:nowrap;">'
            + _esc(subject) + TD_CLOSE
            + '<td style="' + _TD + '">' + _esc(description) + TD_CLOSE
            + "</tr>")
    return "".join(rows)


def build_help(email):
    parts = [_heading("Commands you can send us")]
    parts.append(_para("Send any of these as the subject of an email to this address. "
                       "Subjects are not case sensitive, and replying to one of our "
                       "emails works too."))
    parts.append(
        '<table role="presentation" cellpadding="0" cellspacing="0" style="' + _TABLE + '">'
        "<thead><tr>"
        '<th align="left" style="' + _TH + '">Subject</th>'
        '<th align="left" style="' + _TH + '">What it does</th>'
        "</tr></thead><tbody>" + _help_command_rows() + "</tbody></table>")

    buttons = render_actions(None, HELP_VERBS_WITHOUT_ID)
    if buttons:
        parts.append(buttons)

    reports = list(BugReport.objects.filter(hunter_email__iexact=email,
                                            report_status__in=OPEN_STATUSES))
    reports.sort(key=lambda report: (report.report_datetime is None,
                                     -(report.report_datetime.timestamp()
                                       if report.report_datetime else 0)))
    if reports:
        parts.append(_heading("Your open reports"))
        for report in reports:
            parts.append(_para("<b>" + _esc(report.report_id) + "</b> "
                               + _esc(report.report_title)))
            parts.append('<ul style="' + _LIST + '">'
                         + "".join("<li>" + _esc(line) + "</li>"
                                   for line in allowance_lines(report))
                         + "</ul>")
            parts.append(render_actions(report.report_id, ["CHECK"]))

    return "".join(part for part in parts if part)
