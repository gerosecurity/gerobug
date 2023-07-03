# MAIL TEMPLATES FOR GEROBUG
subject_201 = "Your Bug Report Submission is Received"
message_201 = """\
        <html><body>
            <p>
                Hi there,<br>
                Your submission with title "~TITLE~" has been received with Report ID <b>~ID~</b>
                <br>
                Please wait for further update, thank you.<br>

                <br><br>

                Best regards,<br>
                Gerobug Bounty System
            </p>
        </body></html>
        """

subject_202 = "Status of Report ID ~ID~"
message_202 = """\
        <html><body>
            <p>
                Hi there,<br>
                Thank you for your submission<br><br>

                The status of Report ID <b>~ID~</b> (~TITLE~) is <b>~STATUS~</b>
                <br>
                Please wait for further update<br>

                <br><br>

                Best regards,<br>
                Gerobug Bounty System
            </p>
        </body></html>
        """

subject_203 = "Report Update for ~ID~ Received."
message_203 = """\
        <html><body>
            <p>
                Hi there,<br>
                Your <b>Update</b> on Report ID <b>~ID~</b> (~TITLE~) has been received.
                <br>
                Please wait for further update, thank you.<br>

                <br><br>

                Best regards,<br>
                Gerobug Bounty System
            </p>
        </body></html>
        """

subject_204 = "Appeal Request for ~ID~ Received."
message_204 = """\
        <html><body>
            <p>
                Hi there,<br>
                Your <b>Appeal</b> request for Report ID <b>~ID~</b> (~TITLE~) has been received.
                <br>
                Please wait for further update, thank you.<br>

                <br><br>

                Best regards,<br>
                Gerobug Bounty System
            </p>
        </body></html>
        """

subject_205 = "Agree Submission for ~ID~ Received."
message_205 = """\
        <html><body>
            <p>
                Hi there,<br>
                Thank you for your agreement on our Bounty Calculation<br>
                Your bounty will be processed immediately.
                <br>
                Please wait for further update, thank you.<br>

                <br><br>

                Best regards,<br>
                Gerobug Bounty System
            </p>
        </body></html>
        """

subject_206 = "Bounty Prerequisites for ~ID~ Received."
message_206 = """\
        <html><body>
            <p>
                Hi there,<br>
                NDA and Bounty Prerequisites for Report ID <b>~ID~</b> has been received.
                <br>
                Please wait for further update, thank you.<br>

                <br><br>

                Best regards,<br>
                Gerobug Bounty System
            </p>
        </body></html>
        """

subject_207 = "Your Current Score"
message_207 = """\
        <html><body>
            <p>
                Hi there,<br>
                Your current score in our Bug Bounty Program is <b>~NOTE~</b>
                <br>
                You can check the overall rank in our Wall of Fame page.
                
                <br><br>
                <b>Stay hungry, stay hunting!</b>
                <br><br>

                Best regards,<br>
                Gerobug Bounty System
            </p>
        </body></html>
        """

subject_208 = "Report Status Overview"
message_208 = """\
        <html><body>
            <p>
                Hi there,<br>
                Currently you have <b>~ID~</b> reports submitted to our system.
                <br>
                Here are the details:
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

                Best regards,<br>
                Gerobug Bounty System
            </p>
        </body></html>
        """

# ERROR TEMPLATES FOR GEROBUG
subject_403 = "This email are not Authorized!"
message_403 = """\
        <html><body>
            <p>
                Hi there,<br>
                Thank you for your submission<br><br>

                However, this email address is <b>NOT AUTHORIZED</b><br>
                to perform the requested action for Report ID: <b>~ID~</b>
                <br><br>
                Keep in mind:<br> 
                1. Use the proper email for the Report ID<br>
                2. Re-check your submitted Report ID<br>
                3. Wait for prior instruction before submitting specific request<br>

                <br><br>

                Best regards,<br>
                Gerobug Bounty System
            </p>
        </body></html>
        """

subject_404 = "INVALID REPORT"
message_404 = """\
        <html><body>
            <p>
                Hi there,<br>
                Thank you for your submission<br><br>

                However, your submission is <b>NOT VALID</b>
                <br>
                Please re-check your format, make sure you are following the required format as defined at www.gerobug.id<br>

                <br><br>

                Best regards,<br>
                Gerobug Bounty System
            </p>
        </body></html>
        """

subject_405 = "INVALID REPORT ID"
message_405 = """\
        <html><body>
            <p>
                Hi there,<br>
                Thank you for your submission<br><br>

                However, your submitted Report ID (<b>~ID~</b>) is <b>NOT VALID</b>
                <br> 
                Please re-check your <b>REPORT ID</b>, make sure it is correct.<br>

                <br><br>

                Best regards,<br>
                Gerobug Bounty System
            </p>
        </body></html>
        """

subject_406 = "This Email is Blacklisted"
message_406 = """\
        <html><body>
            <p>
                Hi there,<br>
                This email is <b>BLACKLISTED</b> due to SPAM ACTIVITY<br><br>

                Blacklist period will end in <b>~NOTE~</b> seconds.
                <br> 
                Try to submit again after the blacklist period ends.<br>

                <br><br>

                Best regards,<br>
                Gerobug Bounty System
            </p>
        </body></html>
        """


# NOTIFICATION TEMPLATES FOR GEROBUG
subject_300 = "Notification for Report ID ~ID~"
message_300 = """\
        <html><body>
            <p>
                Hi there,<br>
                With this email, we want to notify you that the current status<br>
                of Report ID <b>~ID~</b> (~TITLE~)<br>
                is <b>~STATUS~</b>
                <br>
                The reason was:<br> 
                <b>~NOTE~</b>

                <br><br>
                Thank you for your effort in keeping our system safe.
                <br><br>
                
                Best regards,<br>
                Gerobug Bounty System
            </p>
        </body></html>
        """

subject_301 = "Notification for Report ID ~ID~"
message_301 = """\
        <html><body>
            <p>
                Hi there,<br>
                With this email, we want to notify you that the current status<br>
                of Report ID <b>~ID~</b> (~TITLE~)<br>
                is <b>~STATUS~</b>
                <br> 
                Please wait for further update<br>

                <br><br>

                Best regards,<br>
                Gerobug Bounty System
            </p>
        </body></html>
        """



# REQUEST TEMPLATES FOR GEROBUG
subject_701 = "Request More Information for Report ID ~ID~"
message_701 = """\
        <html><body>
            <p>
                Hi there,<br>
                With this email, we want to request more information/details<br>
                for Report ID <b>~ID~</b> (~TITLE~)<br>

                <br>
                Note:<br> 
                <b>~NOTE~</b>
                
                <br><br>
                You may submit your updated report with subject "<b>UPDATE_~ID~</b>" using this email address<br>
                Add a <b>Summary</b> of the update in the email body (text only)<br>
                Do not forget to attach a <b>PDF File</b><br>
                
                <br>For more information about email format, you may refer to our guideline page<br>
                
                <br><br>
                We look forward to hearing from you<br>
                Best regards,<br>
                Gerobug Bounty System
            </p>
        </body></html>
        """

subject_702 = "Bounty Calculation for Report ID ~ID~"
message_702 = """\
        <html><body>
            <p>
                Hi there,<br>
                With this email, we want to inform you about Bounty Calculation<br>
                for Report ID <b>~ID~</b> (~TITLE~)<br>
                
                <br>
                Severity: <b>~SEVERITY~</b><br>

                <br>
                Note:<br> 
                <b>~NOTE~</b>
                
                <br><br>
                If you <b>Agree</b>, submit an email with subject "<b>AGREE_~ID~</b>" without any text in the body using this email address<br>
                <br>
                If you <b>Disagree</b>, submit your complaint with subject "<b>APPEAL_~ID~</b>" using this email address<br>
                Add a <b>Reason/Explanation</b> of your complaint in the email body (text only)<br>

                <b>You have a limit of <b>3 times</b> to submit any complaint, otherwise we will consider that you agreed and process the bounty</b>
                <br>
                
                <br>For more information about email format, you may refer to our guideline page<br>

                <br><br>
                We look forward to hearing from you<br>
                Best regards,<br>
                Gerobug Bounty System
            </p>
        </body></html>
        """

subject_703 = "Bounty Prerequisites for Report ID ~ID~"
message_703 = """\
        <html><body>
            <p>
                Hi there,<br>
                With this email, we want to request information that we need to process bounty<br>
                for Report ID <b>~ID~</b> (~TITLE~)<br>

                <br>
                Note:<br> 
                <b>~NOTE~</b>
                
                <br><br>
                Submit an email with subject "<b>NDA_~ID~</b>" using this email address<br>
                Add the requested information in the email body (text only)<br>
                Do not forget to attach the <b>signed NDA</b><br>
                
                <br>For more information about email format, you may refer to our guideline page<br>

                <br><br>
                We look forward to hearing from you<br>
                Best regards,<br>
                Gerobug Bounty System
            </p>
        </body></html>
        """

subject_704 = "Thank you for your contribution"
message_704 = """\
        <html><body>
            <p>
                Hi there,<br>
                With this email, we want to inform that your bounty have been processed<br>
                <br>
                Note:<br> 
                <b>~NOTE~</b>
                
                <br><br>
                Thank you for your contribution to our security with Report ID <b>~ID~</b> (~TITLE~)<br>
                <br> 
                Stay hungry, Stay hunting!<br>

                <br><br>
                Best regards,<br>
                Gerobug Bounty System
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

    300: subject_300,   # INVALID NOTIFICATION (TITLE, ID, STATUS, NOTE)
    301: subject_301,   # STATUS UPDATE NOTIFICATION (TITLE, ID, STATUS)
    
    403: subject_403,   # UNAUTHORIZED (ID)
    404: subject_404,   # INVALID FORMAT
    405: subject_405,   # INVALID REPORT ID (ID)
    406: subject_406,   # BLACKLIST (NOTE)

    701: subject_701,   # REQUEST UPDATE/AMEND (TITLE, ID, NOTE, URL)
    702: subject_702,   # SEND BOUNTY CALCULATIONS (TITLE, ID, NOTE, URL)
    703: subject_703,   # REQUEST NDA (TITLE, ID, NOTE, URL)
    704: subject_704    # SEND BOUNTY + PROOF (TITLE, ID)
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

    300: message_300,
    301: message_301,

    403: message_403,
    404: message_404,
    405: message_405,
    406: message_406,

    701: message_701,
    702: message_702,
    703: message_703,
    704: message_704
}