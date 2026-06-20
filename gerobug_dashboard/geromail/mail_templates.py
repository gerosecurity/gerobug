# MAIL TEMPLATES FOR GEROBUG
subject_201 = "Report Submission Confirmed: ~ID~"
message_201 = """\
        <html><body>
            <p>
                Hello,<br><br>

                We confirm that your report titled "<b>~TITLE~</b>" has been received.<br>
                This submission has been assigned Report ID: <b>~ID~</b>.<br><br>

                Our security team is currently validating your findings. We will respond once the assessment is complete or if further clarification is required.<br><br>

                We appreciate your assistance in securing our infrastructure.<br><br>

                Best Regards,<br>
                Gerobug Bug Bounty Platform
            </p>
        </body></html>
        """

subject_202 = "Status of Report ID ~ID~"
message_202 = """\
        <html><body>
            <p>
                Hello,<br><br>

                This email provides an update on your bug report.<br><br>

                The current status of Report ID <b>~ID~</b> (<b>~TITLE~</b>) is
                <b>~STATUS~</b>.<br><br>

                We will notify you if there are further updates or if additional
                information is required.<br><br>

                Best Regards,<br>
                Gerobug Bug Bounty Platform
            </p>
        </body></html>
        """

subject_203 = "Confirmation: Update Received for Report ~ID~"
message_203 = """\
        <html><body>
            <p>
                Hello,<br><br>

                This is a confirmation that your update for Report ID
                <b>~ID~</b> (<b>~TITLE~</b>) has been successfully received.<br><br>

                Our team will review the update and follow up if additional
                information is required.<br><br>

                Best Regards,<br>
                Gerobug Bug Bounty Platform
            </p>
        </body></html>
        """

subject_204 = "Confirmation: Appeal Request Received for Report ~ID~"
message_204 = """\
        <html><body>
            <p>
                Hello,<br><br>

                This is a confirmation that your appeal request for Report ID
                <b>~ID~</b> (<b>~TITLE~</b>) has been successfully received.<br><br>

                Our team will review the appeal and notify you if additional
                information is required or once a decision has been made.<br><br>

                Best Regards,<br>
                Gerobug Bug Bounty Platform
            </p>
        </body></html>
        """

subject_205 = "Confirmation: Agreement Received for Report ~ID~"
message_205 = """\
        <html><body>
            <p>
                Hello,<br><br>

                This is a confirmation that your agreement regarding the bounty
                calculation for Report ID <b>~ID~</b> has been received.<br><br>

                The bounty processing will proceed according to the program
                guidelines. You will be notified once there are further updates.<br><br>

                Best Regards,<br>
                Gerobug Bug Bounty Platform
            </p>
        </body></html>
        """

subject_206 = "Confirmation: Documents Received for Report ~ID~"
message_206 = """\
        <html><body>
            <p>
                Hello,<br>
                We acknowledge receipt of the NDA and bounty prerequisites for Report ID <b>~ID~</b>.
                <br>
                Our team will review the documents and notify you regarding the next steps shortly.<br>

                <br><br>

                Best Regards,<br>
                Gerobug Bug Bounty Platform
            </p>
        </body></html>
        """

subject_209 = "Confirmation: Data Received for Report ~ID~"
message_209 = """\
        <html><body>
            <p>
                Hello,<br>
                We acknowledge receipt of the bounty prerequisites for Report ID <b>~ID~</b>.
                <br>
                Our team will review the data and notify you regarding the next steps shortly.<br>

                <br><br>

                Best Regards,<br>
                Gerobug Bug Bounty Platform
            </p>
        </body></html>
        """

subject_207 = "Current Score for This Bug Bounty Program"
message_207 = """\
        <html><body>
            <p>
                Hello,<br>
                This is an update regarding your score in the program.<br>
                Your accumulated score currently stands at: <b>~NOTE~</b>.
                <br>
                You may verify your ranking by visiting the Hall of Fame page.
                
                <br><br>
                <b>Good luck with your next hunt.</b>
                <br><br>

                Best Regards,<br>
                Gerobug Bug Bounty Platform
            </p>
        </body></html>
        """

subject_208 = "Submission Summary: Report Overview"
message_208 = """\
        <html><body>
            <p>
                Hello,<br>
                We are providing an overview of your report history.<br>
                You have submitted a total of <b>~ID~</b> reports.
                <br>
                The current status of each report is listed below:
                <br><br>
                
                <table border="1">
                <tr>
                    <th>Report ID</th>
                    <th>Title</th>
                    <th>Status</th>
                </tr>
                ~NOTE~
                </table>
                
                <br><br>

                Best Regards,<br>
                Gerobug Bug Bounty Platform
            </p>
        </body></html>
        """

# ERROR TEMPLATES FOR GEROBUG
subject_403 = "Authorization Failure: Report ~ID~"
message_403 = """\
        <html><body>
            <p>
                Hello,<br>
                We have received your submission.<br><br>

                However, we could not process the request because this email address is not authorized to perform actions for Report ID: <b>~ID~</b>.
                <br><br>
                Please verify the following details:<br> 
                1. Ensure you are sending from the email address associated with this report.<br>
                2. specific Verify that the Report ID is correct.<br>
                3. Ensure you have received instructions to submit this specific request.<br>

                <br><br>

                Best Regards,<br>
                Gerobug Bug Bounty Platform
            </p>
        </body></html>
        """

subject_404 = "Submission Error: Invalid Report Format"
message_404 = """\
        <html><body>
            <p>
                Hello,<br>
                We have received your submission.<br><br>

                Regrettably, this report has been marked as <b>Invalid</b> and cannot be processed in its current state.
                <br>
                Reason for rejection:<br> 
                <b>~NOTE~</b>
                <br>
                Please verify your input and ensure it adheres to the required format as defined <a href="https://gerobug.gitbook.io/documentation/filter-and-validation" target="_blank">in our documentation</a>.<br>

                <br><br>

                Best Regards,<br>
                Gerobug Bug Bounty Platform
            </p>
        </body></html>
        """

subject_405 = "Submission Error: Invalid Report ID ~ID~"
message_405 = """\
        <html><body>
            <p>
                Hello,<br>
                We have received your request.<br><br>

                However, we were unable to process it because the submitted Report ID (<b>~ID~</b>) was not found in our system.
                <br>
                Please verify the Report ID against your records to ensure it is correct and try again.<br>

                <br><br>

                Best Regards,<br>
                Gerobug Bug Bounty Platform
            </p>
        </body></html>
        """

subject_406 = "Submission Blocked: Temporary Restriction"
message_406 = """\
        <html><body>
            <p>
                Hello,<br>
                Your email address has been temporarily blacklisted due to detected spam activity.<br><br>

                This restriction will be lifted in <b>~NOTE~</b> seconds.
                <br> 
                Please wait for this period to expire before attempting to submit again.<br>

                <br><br>

                Best Regards,<br>
                Gerobug Bug Bounty Platform
            </p>
        </body></html>
        """


# NOTIFICATION TEMPLATES FOR GEROBUG
subject_300 = "Notification: Status Update for Report ~ID~"
message_300 = """\
        <html><body>
            <p>
                Hello,<br>
                This email is to notify you of a status change regarding your report.<br>
                The current status for Report ID <b>~ID~</b> ("~TITLE~") is now: <b>~STATUS~</b>.
                <br><br>
                Reason / Additional Notes:<br> 
                <b>~NOTE~</b>

                <br><br>
                Thank you for your continued efforts in helping secure our systems.
                <br><br>
                
                Best Regards,<br>
                Gerobug Bug Bounty Platform
            </p>
        </body></html>
        """

subject_301 = "Notification: Status Update for Report ~ID~"
message_301 = """\
        <html><body>
            <p>
                Hello,<br>
                We are writing to notify you of a change regarding your submission.<br>
                The current status of Report ID <b>~ID~</b> (~TITLE~) is now: <b>~STATUS~</b>.
                <br> 
                Please await further updates as we continue our review process.<br>

                <br><br>

                Best Regards,<br>
                Gerobug Bug Bounty Platform
            </p>
        </body></html>
        """



# REQUEST TEMPLATES FOR GEROBUG
subject_701 = "Action Required: Additional Info for Report ~ID~"
message_701 = """\
        <html><body>
            <p>
                Hello,<br>
                Our team requires additional details regarding Report ID <b>~ID~</b> (~TITLE~) to proceed with the validation process.<br>

                <br>
                Request Details:<br> 
                <b>~NOTE~</b>
                
                <br><br>
                Please submit the requested information by replying to this email. You must strictly follow this format:<br>
                1. Set the Email Subject to: "<b>UPDATE_~ID~</b>"<br>
                2. Include a text-only <b>Summary</b> of the update in the email body.<br>
                3. Ensure the full detailed report is attached as a <b>PDF File</b>.<br>
                
                <br>For detailed formatting rules, please refer to our guideline page.<br>
                
                <br><br>
                We look forward to your response.<br>
                Best Regards,<br>
                Gerobug Bug Bounty Platform
            </p>
        </body></html>
        """

subject_702 = "Bounty Decision: Report ~ID~"
message_702 = """\
        <html><body>
            <p>
                Hello,<br>
                We have completed the bounty calculation for Report ID <b>~ID~</b> ("~TITLE~").<br>
                
                <br>
                Determined Severity: <b>~SEVERITY~</b><br>

                <br>
                Assessment Notes:<br> 
                <b>~NOTE~</b>
                
                <br><br>
                Please review this valuation and choose one of the following actions:<br><br>

                <b>Option 1: Accept the Bounty</b><br>
                Send an email with the subject "<b>AGREE_~ID~</b>". Leave the email body empty.<br>
                <br>
                <b>Option 2: Appeal the Decision</b><br>
                Send an email with the subject "<b>APPEAL_~ID~</b>". You must include your <b>Reason/Justification</b> in the email body (text only).<br>

                <br>
                <b>Important:</b> You are limited to a maximum of <b>3 appeals</b>. If this limit is exceeded, the current determination will be considered final and processed accordingly.
                <br>
                
                <br>For detailed formatting rules, please refer to our guideline page.<br>

                <br><br>
                We look forward to your response.<br>
                Best Regards,<br>
                Gerobug Bug Bounty Platform
            </p>
        </body></html>
        """

subject_703 = "Action Required: Bounty Prerequisites for Report ~ID~"
message_703 = """\
        <html><body>
            <p>
                Hello,<br>
                We are preparing to process the reward payout for Report ID <b>~ID~</b> ("~TITLE~").<br>
                Before we can proceed, we require specific documentation and details.<br>

                <br>
                Requirements / Instructions:<br> 
                <b>~NOTE~</b>
                
                <br><br>
                To complete this step, please reply to this email following these strict guidelines:<br>
                1. Set the Email Subject to: "<b>NDA_~ID~</b>"<br>
                2. Provide the requested information in the email body (text only).<br>
                3. You must attach the <b>signed NDA</b> document.<br>
                
                <br>For detailed formatting rules, please refer to our guideline page.<br>

                <br><br>
                We look forward to receiving your documents.<br>
                Best Regards,<br>
                Gerobug Bug Bounty Platform
            </p>
        </body></html>
        """

subject_704 = "Processing Complete: Report ~ID~"
message_704 = """\
        <html><body>
            <p>
                Hello,<br>
                Congratulations! We are pleased to confirm that the reward processing for your submission has been completed.<br>
                <br>
                Notes:<br> 
                <b>~NOTE~</b>
                
                <br><br>
                Your Certificate of Appreciation is attached to this email. Additionally, your score has been updated on our Hall of Fame to reflect this achievement.<br>
                <br>
                Thank you for your valuable contribution to our security with Report ID <b>~ID~</b> ("~TITLE~").<br>
                <br> 
                Good luck with your next hunt.<br>

                <br><br>
                Best Regards,<br>
                Gerobug Bug Bounty Platform
            </p>
        </body></html>
        """

subject_9999 = "Gerobug: Password Reset Request"
message_9999 = """\
        <html><body>
            <p>
                Hello,<br>
                We received a request to reset the password associated with this email address.<br><br>
                
                <b>Please click the link below to set a new password:</b><br>
                <a href="~DOMAIN~:6320/login/reset/~UID~/~TOKEN~/">Reset Gerobug Account Password</a>
                <br><br>

                This is a secure, one-time link. It will expire after use.<br>
                If you did not request a password reset, you may safely ignore this email.<br>
                <br><br>

                Best Regards,<br>
                Gerobug Bug Bounty Platform
            </p>
        </body></html>
        """


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
    209: subject_209,   # DATA RECEIVED - INFO ONLY (ID)

    300: subject_300,   # INVALID NOTIFICATION (TITLE, ID, STATUS, NOTE)
    301: subject_301,   # STATUS UPDATE NOTIFICATION (TITLE, ID, STATUS)
    
    403: subject_403,   # UNAUTHORIZED (ID)
    404: subject_404,   # INVALID FORMAT
    405: subject_405,   # INVALID REPORT ID (ID)
    406: subject_406,   # BLACKLIST (NOTE)

    701: subject_701,   # REQUEST UPDATE/AMEND (TITLE, ID, NOTE, URL)
    702: subject_702,   # SEND BOUNTY CALCULATIONS (TITLE, ID, NOTE, URL)
    703: subject_703,   # REQUEST NDA (TITLE, ID, NOTE, URL)
    704: subject_704,   # SEND BOUNTY + PROOF (TITLE, ID)

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

    403: message_403,
    404: message_404,
    405: message_405,
    406: message_406,

    701: message_701,
    702: message_702,
    703: message_703,
    704: message_704,

    9999: message_9999
}
