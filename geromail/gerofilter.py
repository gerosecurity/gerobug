import re
import os
import PyPDF2

from dashboards.models import BugReport, BugReportUpdate, BugReportAppeal, BugReportNDA, BugHunter



# CHECK IF POSSIBLE DUPLICATE (NEED IMPROVEMENTS)
def check_duplicate(id):
    report = BugReport.objects.get(report_id=id)
    attack = report.report_attack
    endpoint = report.report_endpoint
    
    endpoint_reports = BugReport.objects.filter(report_endpoint=endpoint)
    
    for x in endpoint_reports:
        if (x.report_id != id) and (x.report_attack == attack):
            report.report_duplicate = 1
            report.save()
            print('[LOG] Possible Duplicate Report')
            break

# VALIDATE APPEAL LIMIT
def validate_appeal(id):
    report = BugReport.objects.get(report_id=id)
    appeal = report.report_appeal
    
    if appeal < 3: # HUNTER LIMIT 3x APPEAL
        return True
    else:
        return False
    
# VALIDATE IF CERTAIN OPERATION IS PERMITTED
def validate_permission(operation, id):
    report = BugReport.objects.get(report_id=id)
    permission = report.report_permission
    permited = []

    if permission <= 0: # NO PERMISSION
        print("[LOG] No Permission")
        return False
    else:
        if permission >= 4: # UPDATE
            permission = permission - 4
            permited.append("U")

        if permission >= 2: # APPEAL
            permission = permission - 2
            permited.append("A")

        if permission >= 1: # NDA
            permission = permission - 1
            permited.append("N")

        print("[LOG] Permission =", report.report_permission, permited)
        if operation in permited:
            print("[LOG]",operation,"is Permitted")
            return True
        else:
            print("[LOG]",operation,"is NOT Permitted")
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
    if(len(id) >= 12) & (id.isalnum()):
        if BugReport.objects.filter(report_id=id).exists():
            return True
        else:    
            return False
    else:    
        return False


# VALIDATE PDF FILE
def check_pdf(file):
    try:
        PyPDF2.PdfFileReader(open(file, "rb"))
    except Exception as e:
        print(e)
        print("[ERROR] Invalid PDF File")
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
            file = part.get_payload(decode=True)
            fileSize = len(file)
            print('File size = ' + str(fileSize))
        
            if fileSize >= 25000000:
                pass
            elif not os.path.isfile(filePath):
                if not os.path.exists(fileDir):
                    os.mkdir(fileDir)

                fp = open(filePath, 'wb')
                fp.write(file)
                fp.close()
                
                # VALIDATE PDF FILE
                if check_pdf(filePath):
                    valid = True
                else:
                    # ROLLBACK
                    os.remove(filePath)
                    os.rmdir(fileDir)

                break
    
    return valid


# PARSE EMAIL BODY
def parse_body(body):
    endpoint = '' 
    summary = ''
    
    try:
        rtype = re.search('TYPE=\[(.+?)\]', body)
        if rtype != None:
            rtype = rtype.group(1)
        else:
            rtype = ''

        endpoint = re.search('ENDPOINT=\[(.+?)\]', body)
        if endpoint != None:
            endpoint = endpoint.group(1)
        else:
            endpoint = ''

        summary = re.search('SUMMARY=(.*)', body)
        if summary != None:
            summary = summary.group(1)
        else:
            summary = ''

    except Exception as e:
        print(str(e))

    return rtype, endpoint, summary


# CLASSIFY ACTION BY EMAIL SUBJECT
def classify_action(email, subject):
    try:
        if(re.search(r'^SUBMIT_', subject)):
            title = subject[7 : ]
            return 201, title

        elif(re.search(r'^CHECK_', subject)):
            id = subject[6 : ]
            if validate_id(id):
                if validate_user(email, id):
                    return 202, id
                else:
                    return 403, id
            else:
                return 405, id

        elif(re.search(r'^UPDATE_', subject)):
            id = subject[7 : ]
            if validate_id(id):
                if validate_user(email, id):
                    if validate_permission("U", id):
                        return 203, id
                    else:
                        return 403, id
                else:
                    return 403, id
            else:
                return 405, id

        elif(re.search(r'^APPEAL_', subject)):
            id = subject[7 : ]
            if validate_id(id):
                if validate_user(email, id):
                    if validate_permission("A", id):
                        if validate_appeal(id):
                            return 204, id
                        else:
                            return 403, id
                    else:
                        return 403, id
                else:
                    return 403, id
            else:
                return 405, id

        elif(re.search(r'^AGREE_', subject)):
            id = subject[6 : ]
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

        elif(re.search(r'^MY_SCORE$', subject)):
            if BugHunter.objects.filter(hunter_email=email).exists():
                hunter = BugHunter.objects.get(hunter_email=email)
                return 207, str(hunter.hunter_scores)
            else:
                return 403
                
        else:
            return 404, " "

    except Exception as e:
        print(str(e))