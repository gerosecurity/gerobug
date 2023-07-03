import re

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
    
    Final = round((((LS + IS) * 10) / 18),2)
    return Final