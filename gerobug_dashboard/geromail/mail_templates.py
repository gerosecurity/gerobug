# MAIL TEMPLATES FOR GEROBUG

_P    = "margin:0 0 16px 0;"
_LAST = "margin:0;"
_LIST = "margin:0 0 16px 0; padding-left:22px;"
_NOTE = ("margin:0 0 16px 0; padding:12px 16px; background-color:#f0f4f8; "
         "border-left:4px solid #1f2933; border-radius:4px;")
_LINK = "color:#1f6feb;"
_BTN  = ("display:inline-block; padding:10px 18px; background-color:#1f2933; "
         "color:#ffffff; text-decoration:none; border-radius:4px;")


def _para(text, style=_P):
    return '<p style="' + style + '">' + text + "</p>"


def _note(label, token):
    return ('<p style="margin:0 0 6px 0; font-weight:bold;">' + label + "</p>"
            '<div style="' + _NOTE + '">' + token + "</div>")


def _list(items):
    return ('<ol style="' + _LIST + '">'
            + "".join("<li>" + item + "</li>" for item in items)
            + "</ol>")


def _wrap(content):
    return (
        "<html>"
        '<body style="margin:0; padding:0; background-color:#f4f4f5;">'
        '<div style="max-width:640px; margin:0 auto; padding:24px; '
        "font-family:Arial, Helvetica, sans-serif; color:#1f2933; "
        'font-size:14px; line-height:1.6;">'
        + content +
        '<p style="margin:24px 0 0 0; padding-top:16px; '
        "border-top:1px solid #e4e7eb; color:#7b8794; font-size:12px;\">"
        "This is an automated message from the Gerobug Bug Bounty Platform. "
        "If you received it in error, you may safely disregard it."
        "</p>"
        "</div>"
        "</body>"
        "</html>"
    )


_HELLO   = _para("Hello,")
_SIGNOFF = _para("Best Regards,<br>Gerobug Bug Bounty Platform", _LAST)


subject_201 = "Report Submission Confirmed: ~ID~"
message_201 = _wrap(
    _HELLO
    + _para('We confirm that your report titled "<b>~TITLE~</b>" has been received. '
            "This submission has been assigned Report ID: <b>~ID~</b>.")
    + _para("Our security team is currently validating your findings. We will respond "
            "once the assessment is complete or if further clarification is required.")
    + _para("We appreciate your assistance in securing our infrastructure.")
    + _SIGNOFF
)

subject_202 = "CHECK_~ID~ | Status of Report ~ID~"
message_202 = _wrap(
    _HELLO
    + _para("Here is where your report stands and what, if anything, we need from you.")
    + "~NOTE~"
    + _SIGNOFF
)

subject_203 = "Confirmation: Update Received for Report ~ID~"
message_203 = _wrap(
    _HELLO
    + _para("This is a confirmation that your update for Report ID <b>~ID~</b> "
            "(<b>~TITLE~</b>) has been successfully received.")
    + _para("Our team will review the update and follow up if additional "
            "information is required.")
    + _note("Update Allowance:", "~NOTE~")
    + _SIGNOFF
)

subject_204 = "Confirmation: Appeal Request Received for Report ~ID~"
message_204 = _wrap(
    _HELLO
    + _para("This is a confirmation that your appeal request for Report ID <b>~ID~</b> "
            "(<b>~TITLE~</b>) has been successfully received.")
    + _para("Our team will review the appeal and notify you if additional information "
            "is required or once a decision has been made.")
    + _note("Appeal Allowance:", "~NOTE~")
    + _SIGNOFF
)

subject_205 = "Confirmation: Agreement Received for Report ~ID~"
message_205 = _wrap(
    _HELLO
    + _para("This is a confirmation that your agreement regarding the bounty calculation "
            "for Report ID <b>~ID~</b> has been received.")
    + _para("Your report has moved to <b>Bounty in Process</b>, the stage where we "
            "prepare the reward. We will email you with the next steps, and we may ask "
            "for a few details before the payout.")
    + _para("No action is required from you right now.")
    + _SIGNOFF
)

subject_206 = "Confirmation: Documents Received for Report ~ID~"
message_206 = _wrap(
    _HELLO
    + _para("We acknowledge receipt of the NDA and bounty prerequisites for "
            "Report ID <b>~ID~</b>.")
    + _para("Our team will review the documents and notify you regarding the next "
            "steps shortly.")
    + _SIGNOFF
)

subject_209 = "Confirmation: Data Received for Report ~ID~"
message_209 = _wrap(
    _HELLO
    + _para("We acknowledge receipt of the bounty prerequisites for Report ID <b>~ID~</b>.")
    + _para("Our team will review the data and notify you regarding the next steps shortly.")
    + _SIGNOFF
)

subject_207 = "Current Score for This Bug Bounty Program"
message_207 = _wrap(
    _HELLO
    + _para("This is an update regarding your score in the program. "
            "Your accumulated score currently stands at: <b>~NOTE~</b>.")
    + _para("You may verify your ranking by visiting the Hall of Fame page.")
    + _para("<b>Good luck with your next hunt.</b>")
    + _SIGNOFF
)

subject_208 = "Submission Summary: Report Overview"
message_208 = _wrap(
    _HELLO
    + _para("Here is an overview of your report history with our bug bounty program. "
            "You have submitted a total of <b>~ID~</b> report(s). The current status "
            "of each is listed below.")
    + '<table role="presentation" cellpadding="0" cellspacing="0" '
      'style="width:100%; border-collapse:collapse; margin:8px 0 20px 0; font-size:14px;">'
        "<thead><tr>"
            '<th align="left" style="padding:10px 12px; background-color:#1f2933; '
            'color:#ffffff; border:1px solid #1f2933;">Report ID</th>'
            '<th align="left" style="padding:10px 12px; background-color:#1f2933; '
            'color:#ffffff; border:1px solid #1f2933;">Title</th>'
            '<th align="left" style="padding:10px 12px; background-color:#1f2933; '
            'color:#ffffff; border:1px solid #1f2933;">Status</th>'
        "</tr></thead>"
        "<tbody>~NOTE~</tbody>"
      "</table>"
    + _para("For the details of one report, send an email with the subject "
            "<b>CHECK_</b> followed by its Report ID. To ask our team a question "
            "about a report, use the subject <b>COMMENT_</b> followed by its "
            "Report ID.")
    + _SIGNOFF
)


subject_403 = "Authorization Failure: Report ~ID~"
message_403 = _wrap(
    _HELLO
    + _para("We have received your submission. However, we could not process the request "
            "because this email address is not authorized to perform actions for "
            "Report ID: <b>~ID~</b>.")
    + _para("Please verify the following details:")
    + _list([
        "Ensure you are sending from the email address associated with this report.",
        "Verify that the Report ID is correct.",
        "Ensure you have received instructions to submit this specific request.",
    ])
    + _SIGNOFF
)

subject_404 = "We could not process your email"
message_404 = _wrap(
    _HELLO
    + _para("We received your email, but we could not process it. Nothing has been "
            "changed on your report.")
    + _note("What went wrong:", "~NOTE~")
    + _para("Please verify your input and ensure it adheres to the required format as "
            'defined <a href="https://gerobug.gitbook.io/documentation/filter-and-validation" '
            'style="' + _LINK + '" target="_blank">in our documentation</a>.')
    + _SIGNOFF
)

subject_405 = "Submission Error: Invalid Report ID ~ID~"
message_405 = _wrap(
    _HELLO
    + _para("We have received your request. However, we were unable to process it because "
            "the submitted Report ID (<b>~ID~</b>) was not found in our system.")
    + _para("Please verify the Report ID against your records to ensure it is correct "
            "and try again.")
    + _SIGNOFF
)

subject_410 = "No Reports Yet"
message_410 = _wrap(
    _HELLO
    + _para("We looked for reports submitted from this email address and found none, "
            "so there is nothing to show yet.")
    + _para("To submit your first report, send an email with the subject "
            "\"<b>SUBMIT_Your report title</b>\", put TYPE, ENDPOINT and SUMMARY in the "
            "body, and attach your full report as a PDF file.")
    + _para("If you have submitted a report before, send your request from the same "
            "email address you used then.")
    + _SIGNOFF
)

subject_406 = "Submission Blocked: Temporary Restriction"
message_406 = _wrap(
    _HELLO
    + _para("Your email address has been temporarily blacklisted due to detected "
            "spam activity.")
    + _para("This restriction will be lifted in <b>~NOTE~</b> seconds. Please wait for "
            "this period to expire before attempting to submit again.")
    + _SIGNOFF
)


subject_300 = "Notification: Status Update for Report ~ID~"
message_300 = _wrap(
    _HELLO
    + _para("This email is to notify you of a status change regarding your report. "
            'The current status for Report ID <b>~ID~</b> ("~TITLE~") is now: <b>~STATUS~</b>.')
    + _note("Reason / Additional Notes:", "~NOTE~")
    + _para("Thank you for your continued efforts in helping secure our systems.")
    + _SIGNOFF
)

subject_301 = "Notification: Status Update for Report ~ID~"
message_301 = _wrap(
    _HELLO
    + _para("We are writing to notify you of a change regarding your submission. "
            "The current status of Report ID <b>~ID~</b> (~TITLE~) is now: <b>~STATUS~</b>.")
    + _para("Please await further updates as we continue our review process.")
    + _SIGNOFF
)


subject_302 = "Bounty Accepted by Default: Report ~ID~"
message_302 = _wrap(
    _HELLO
    + _para('Our bounty calculation for Report ID <b>~ID~</b> ("~TITLE~") was sent to '
            "you 30 days ago and we have not received an appeal within that period.")
    + _para("Determined Severity: <b>~SEVERITY~</b>")
    + _para("As set out in the bounty decision email, the valuation is therefore "
            "considered accepted and the report has moved to <b>~STATUS~</b>. No "
            "action is required from you at this stage.")
    + _para("We will contact you with the next steps for the reward process.")
    + _SIGNOFF
)


subject_409 = "Appeal Limit Reached: Report ~ID~"
message_409 = _wrap(
    _HELLO
    + _para("We have received your appeal for Report ID <b>~ID~</b>, but it could not "
            "be recorded: you have already used all <b>3</b> appeals available to you "
            "on this report.")
    + _para("As stated in our bounty decision email, the valuation standing after the "
            "third appeal is final. It is treated as accepted: you may confirm it now "
            "by sending an email with the subject \"<b>AGREE_~ID~</b>\", or it will be "
            "accepted automatically 30 days after the latest bounty decision email. "
            "No further action is required from you.")
    + _para("We do appreciate the time you put into the submission, and we hope to see "
            "your next one.")
    + _SIGNOFF
)


subject_408 = "Updates Closed: Report ~ID~"
message_408 = _wrap(
    _HELLO
    + _para("We have received your update for Report ID <b>~ID~</b>, but it could not "
            "be recorded: the report has already moved past the assessment stage and is "
            "now at <b>~STATUS~</b>.")
    + _para("At this point the finding itself is settled and the remaining steps concern "
            "the reward process only, so updates to the report are closed.")
    + _para("If your message concerns the reward process rather than the finding, our "
            "team will reach out to you about it directly.")
    + _SIGNOFF
)


subject_407 = "Update Limit Reached: Report ~ID~"
message_407 = _wrap(
    _HELLO
    + _para("We have received your update for Report ID <b>~ID~</b>, but it could not "
            "be recorded: you have already used all <b>3</b> updates available to you "
            "on this report without a request from our team.")
    + _para("This is not a rejection of your finding. Our team can invite a further "
            "update at any time, and an update sent in response to such a request "
            "does not count against the limit.")
    + _para("Please wait for our team to contact you if more information is needed.")
    + _SIGNOFF
)

subject_701 = "UPDATE_~ID~ | Action Required: Additional Info"
message_701 = _wrap(
    _HELLO
    + _para("Our team requires additional details regarding Report ID <b>~ID~</b> "
            "(~TITLE~) to proceed with the validation process.")
    + _note("Request Details:", "~NOTE~")
    + _para("Reply to this email, or send a new email with the subject "
            "<b>UPDATE_~ID~</b>. Either way, please include:")
    + _list([
        "A text-only <b>Summary</b> of the update in the email body.",
        "The full detailed report attached as a <b>PDF file</b>.",
    ])
    + "~ACTIONS~"
    + _para("An update sent in reply to this request does <b>not</b> count against "
            "the 3 updates you may send on your own initiative.")
    + _para("For detailed formatting rules, please refer to our guideline page.")
    + _para("We look forward to your response.")
    + _SIGNOFF
)

subject_702 = "Bounty Decision: Report ~ID~"
message_702 = _wrap(
    _HELLO
    + _para('We have completed the bounty calculation for Report ID <b>~ID~</b> ("~TITLE~").')
    + _para("Determined Severity: <b>~SEVERITY~</b>")
    + _note("Assessment Notes:", "~NOTE~")
    + _para("Please review this valuation and choose one of the following actions:")
    + _para("<b>Option 1: Accept the Bounty</b><br>"
            'Send an email with the subject "<b>AGREE_~ID~</b>". Leave the email body empty.')
    + _para("<b>Option 2: Appeal the Decision</b><br>"
            'Send an email with the subject "<b>APPEAL_~ID~</b>". You must include your '
            "<b>Reason/Justification</b> in the email body (text only).")
    + "~ACTIONS~"
    + _para("<b>Important:</b> You are limited to a maximum of <b>3 appeals</b>. If this "
            "limit is exceeded, the current determination will be considered final and "
            "processed accordingly.")
    + _para("<b>Please note:</b> if we do not hear from you within <b>30 days</b> of this "
            "email, the valuation above will be treated as accepted and the report will "
            "move on to bounty processing automatically.")
    + _para("For detailed formatting rules, please refer to our guideline page.")
    + _para("We look forward to your response.")
    + _SIGNOFF
)

subject_703 = "DATA_~ID~ | Action Required: Bounty Prerequisites (NDA)"
message_703 = _wrap(
    _HELLO
    + _para('We are preparing to process the reward payout for Report ID <b>~ID~</b> '
            '("~TITLE~"). Before we can proceed, we require specific documentation '
            "and details.")
    + _note("Requirements / Instructions:", "~NOTE~")
    + _para("Reply to this email, or send a new email with the subject "
            "<b>DATA_~ID~</b>. Either way, please include:")
    + _list([
        "The requested information in the email body (text only).",
        "The <b>signed NDA</b> document as an attachment.",
    ])
    + "~ACTIONS~"
    + _para("For detailed formatting rules, please refer to our guideline page.")
    + _para("We look forward to receiving your documents.")
    + _SIGNOFF
)

subject_704 = "Processing Complete: Report ~ID~"
message_704 = _wrap(
    _HELLO
    + _para("Congratulations! We are pleased to confirm that the reward processing for "
            "your submission has been completed.")
    + _note("Notes:", "~NOTE~")
    + _para("Your Certificate of Appreciation is attached to this email. Additionally, "
            "your score has been updated on our Hall of Fame to reflect this achievement.")
    + _para("Thank you for your valuable contribution to our security with Report ID "
            '<b>~ID~</b> ("~TITLE~").')
    + _para("Good luck with your next hunt.")
    + _SIGNOFF
)

subject_705 = "DATA_~ID~ | Action Required: Bounty Prerequisites"
message_705 = _wrap(
    _HELLO
    + _para('We are preparing to process the reward payout for Report ID <b>~ID~</b> '
            '("~TITLE~"). Before we can proceed, we require specific documentation '
            "and details.")
    + _note("Requirements / Instructions:", "~NOTE~")
    + _para("Reply to this email, or send a new email with the subject "
            "<b>DATA_~ID~</b>. Either way, please include:")
    + _list([
        "The requested information in the email body (text only).",
    ])
    + "~ACTIONS~"
    + _para("For detailed formatting rules, please refer to our guideline page.")
    + _para("We look forward to receiving your documents.")
    + _SIGNOFF
)


subject_9999 = "Gerobug: Password Reset Request"
message_9999 = _wrap(
    _HELLO
    + _para("We received a request to reset the password associated with this "
            "email address.")
    + _note("Your username (use this to log in):", "~USERNAME~")
    + _para("Please click the button below to set a new password:")
    + '<p style="margin:0 0 16px 0;">'
        '<a href="~DOMAIN~:6320/login/reset/~UID~/~TOKEN~/" style="' + _BTN + '">'
        "Reset Account Password</a>"
      "</p>"
    + _para("This is a secure, one-time link and it will expire after use. "
            "If you did not request a password reset, you may safely ignore this email.")
    + _SIGNOFF
)


# DICTIONARY VARIABLES
subjectlist = {
    201: subject_201,   # SUBMIT SUCCESS (TITLE, ID)
    202: subject_202,   # CHECK STATUS SUCCESS (TITLE, ID, STATUS)
    203: subject_203,   # UPDATE SUCCESS (TITLE, ID)
    204: subject_204,   # APPEAL SUCCESS (TITLE, ID)
    205: subject_205,   # AGREE SUCCESS (ID)
    206: subject_206,   # NDA SUCCESS (ID)
    207: subject_207,   # CHECK SCORE (NOTE)
    208: subject_208,   # CHECK ALL STATUS (ID, NOTE)
    209: subject_209,

    300: subject_300,   # INVALID NOTIFICATION (TITLE, ID, STATUS, NOTE)
    301: subject_301,   # STATUS UPDATE NOTIFICATION (TITLE, ID, STATUS)
    302: subject_302,

    403: subject_403,   # UNAUTHORIZED (ID)
    404: subject_404,   # INVALID FORMAT
    405: subject_405,   # INVALID REPORT ID (ID)
    406: subject_406,   # BLACKLIST (NOTE)
    410: subject_410,
    407: subject_407,
    408: subject_408,
    409: subject_409,

    701: subject_701,   # REQUEST UPDATE/AMEND (TITLE, ID, NOTE, URL)
    702: subject_702,   # SEND BOUNTY CALCULATIONS (TITLE, ID, NOTE, URL)
    703: subject_703,
    704: subject_704,   # SEND BOUNTY + PROOF (TITLE, ID)
    705: subject_705,   # REQUEST PREREQUISITES - NO NDA (TITLE, ID, NOTE)

    9999: subject_9999
}

messagelist = {
    201: message_201,
    202: message_202,
    203: message_203,
    204: message_204,
    205: message_205,
    206: message_206,
    207: message_207,
    208: message_208,
    209: message_209,

    300: message_300,
    301: message_301,
    302: message_302,

    403: message_403,
    404: message_404,
    405: message_405,
    406: message_406,
    410: message_410,
    407: message_407,
    408: message_408,
    409: message_409,

    701: message_701,
    702: message_702,
    703: message_703,
    704: message_704,
    705: message_705,

    9999: message_9999
}
