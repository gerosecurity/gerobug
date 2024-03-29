import re
from cvss import CVSS3



def calculate_owasp(severity_string):
    Final = 0
    # OWASP SEVERITY STRING FORMAT
    # (SL:0/M:0/O:0/S:0/ED:0/EE:0/A:0/ID:0/LC:0/LI:0/LAV:0/LAC:0/FD:0/RD:0/NC:0/PV:0)

    # LIKELIHOOD FACTORS
    SL  = int(severity_string[severity_string.find('SL')+3:severity_string.find('/M')])
    M   = int(severity_string[severity_string.find('/M')+3:severity_string.find('/O')])
    O   = int(severity_string[severity_string.find('/O')+3:severity_string.find('/S')])
    S   = int(severity_string[severity_string.find('/S')+3:severity_string.find('/ED')])
    ED  = int(severity_string[severity_string.find('ED')+3:severity_string.find('/EE')])
    EE  = int(severity_string[severity_string.find('EE')+3:severity_string.find('/A')])
    A   = int(severity_string[severity_string.find('/A')+3:severity_string.find('/ID')])
    ID  = int(severity_string[severity_string.find('ID')+3:severity_string.find('/LC')])

    # IMPACT FACTORS
    LC  = int(severity_string[severity_string.find('LC')+3:severity_string.find('/LI')])
    LI  = int(severity_string[severity_string.find('LI')+3:severity_string.find('/LAV')])
    LAV = int(severity_string[severity_string.find('LAV')+4:severity_string.find('/LAC')])
    LAC = int(severity_string[severity_string.find('LAC')+4:severity_string.find('/FD')])
    FD  = int(severity_string[severity_string.find('FD')+3:severity_string.find('/RD')])
    RD  = int(severity_string[severity_string.find('RD')+3:severity_string.find('/NC')])
    NC  = int(severity_string[severity_string.find('NC')+3:severity_string.find('/PV')])
    PV  = int(severity_string[severity_string.find('PV')+3:severity_string.find(')')])

    LS = (SL+M+O+S+ED+EE+A+ID)/8
    IS = (LC+LI+LAV+LAC+FD+RD+NC+PV)/8
    
    if LS < 3: # LOW
        A = 1
    elif LS < 6: # MEDIUM
        A = 2
    elif LS <= 9: # HIGH
        A = 3

    if IS < 3: # LOW
        B = 1
    elif IS < 6: # MEDIUM
        B = 2
    elif IS <= 9: # HIGH
        B = 3

    # FINAL CALIBRATION
    Final = round(((LS+IS+2)/2),2)
    if A+B == 2:
        Final = 0
        
    elif A+B == 3:
        if Final >= 4:
            Final = 3.99

    elif A+B == 4:
        if Final >= 7:
            Final = 6.99
        elif Final < 4:
            Final = 4

    elif A+B == 5:
        if Final >= 9:
            Final = 8.99
        elif Final < 7:
            Final = 7

    elif A+B == 6:
       if Final <= 9:
           Final = 9
    
    return Final


def calculate_cvss(severity_string):
    cvss = CVSS3(severity_string)
    return cvss.scores()[0]


def calculate(severity_string, severity_type):
    if severity_type == "CVSS":
        return calculate_cvss(severity_string)
    
    elif severity_type == "OWASP":
        return calculate_owasp(severity_string)
    
    else:
        return 0

def classify(severity_string):
    cvss = re.search("^CVSS:3\.1\/AV:[NALP]\/AC:[LH]\/PR:[NLH]\/UI:[NR]\/S:[UC]\/C:[NLH]\/I:[NLH]\/A:[N|L|H](\/E:[UPFH])?(\/RL:[OTWU])?(\/RC:[URC])?(\/CR:[LMH])?(\/IR:[LMH])?(\/AR:[LMH])?(\/MAV:[NALP])?(\/MAC:[LH])?(\/MPR:[NLH])?(\/MUI:[NR])?(\/MS:[UC])?(\/MC:[NLH])?(\/MI:[NLH])?(\/MA:[NLH])?$", severity_string)
    if cvss:
        return "CVSS"
    
    else:
        owasp = re.search("^\(SL:[0-9]\/M:[0-9]\/O:[0-9]\/S:[0-9]\/ED:[0-9]\/EE:[0-9]\/A:[0-9]\/ID:[0-9]\/LC:[0-9]\/LI:[0-9]\/LAV:[0-9]\/LAC:[0-9]\/FD:[0-9]\/RD:[0-9]\/NC:[0-9]\/PV:[0-9]\)$", severity_string)
        if owasp:
            return "OWASP"
        else:
            return ""