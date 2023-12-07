from django.apps import AppConfig
import sys

class DashboardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboards'
    
    if 'gerobug.wsgi' in sys.argv:
    #if 'runserver' in sys.argv: 
        def ready(self):
            import gerocert.gerocert, dashboards.rulestemplate
            import logging
            from logging.handlers import TimedRotatingFileHandler
            from geromail.thread import RunGeromailThread
            from dashboards.models import BugReport, BugHunter, ReportStatus, StaticRules, BlacklistRule, CertificateData, Personalization
            from django.contrib.auth.models import Group, Permission
            from django.core.exceptions import ObjectDoesNotExist
            from prerequisites.models import MailBox

            # GEROLOGGER INITIATION
            def gerologger_config():
                gerologger = logging.getLogger("Gerologger")
                log_handler = TimedRotatingFileHandler('log/gerobug.log', when='midnight', backupCount=31)
                log_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
                gerologger.setLevel(logging.DEBUG)
                gerologger.addHandler(log_handler)

            # INSERT STATUS TO DB
            def init_status_db(id, name):
                if not ReportStatus.objects.filter(status_id=id).exists():
                    status = ReportStatus()
                    
                    status.status_id = id
                    status.status_name = name
                    
                    status.save()
                    logging.getLogger("Gerologger").debug("Init Status DB success")
                
                else:
                    logging.getLogger("Gerologger").debug("Status DB already exists")

            # INSERT DEFAULT RULES (TERMS, SCOPE, ETC) AND BLACKLIST RULE TO DB
            def init_rules_db():
                if  not StaticRules.objects.filter(pk=1).exists():
                    staticrules = StaticRules()
                    
                    staticrules.RDP = dashboards.rulestemplate.RDP_template
                    staticrules.bountyterms = dashboards.rulestemplate.bountyterms_template
                    staticrules.inscope = dashboards.rulestemplate.inscope_templates
                    staticrules.outofscope = dashboards.rulestemplate.outofscope_templates
                    staticrules.reportguidelines = dashboards.rulestemplate.reportguidelines_templates
                    staticrules.faq = dashboards.rulestemplate.faq_templates
                    staticrules.save()
                    logging.getLogger("Gerologger").debug("Init Rules DB success")
                
                else:
                    logging.getLogger("Gerologger").debug("Rules DB already exists")
                
                if not BlacklistRule.objects.filter(rule_id=1).exists():
                    blacklistrule = BlacklistRule()
                    
                    blacklistrule.rule_id = 1
                    blacklistrule.max_counter = 10
                    blacklistrule.buffer_monitor = 60
                    blacklistrule.buffer_blacklist = 3600
                    blacklistrule.buffer_clean = 86400
                    blacklistrule.save()
                    logging.getLogger("Gerologger").debug("Init Blacklist Rules DB success")
                
                else:
                    logging.getLogger("Gerologger").debug("Blacklist Rules DB already exists")

            # INSERT CERTIFICATE DATA TO DB
            def init_cert_db(): 
                if not CertificateData.objects.filter(cert_id=1).exists():
                    certdata = CertificateData()
                    
                    certdata.cert_id = 1
                    certdata.officer_name = "Billy Sudarsono"
                    certdata.officer_title = "Founder of Gerobug"
                    certdata.save()

                    logging.getLogger("Gerologger").debug("Init Certificate Data success")
                
                else:
                    logging.getLogger("Gerologger").debug("Certificate Data already exists")
                
                gerocert.gerocert.generate_sample()

            # INIT MAILBOX
            def init_mailbox_db():
                if not MailBox.objects.filter(mailbox_id=1).exists():
                    mailbox = MailBox()
                    mailbox.mailbox_id = 1
                    mailbox.email = ""
                    mailbox.password = ""
                    mailbox.mailbox_type = ""
                    mailbox.save()
                    logging.getLogger("Gerologger").debug("Init Mailbox success")

                else:
                    logging.getLogger("Gerologger").debug("Mailbox already exists")

            # INIT GROUP REVIEWER CREATION
            def init_group():
                perm_list = Permission.objects.all()
                permissions = {}
                for perm in perm_list:
                    permissions[perm.codename] = perm
                try:
                    checker = Group.objects.get(name="Reviewer")
                except ObjectDoesNotExist:
                    g_reviewer = Group.objects.create(name="Reviewer")
                    g_reviewer.permissions.add(permissions['view_group'])
                    g_reviewer.permissions.add(permissions['view_user'])
                    g_reviewer.permissions.add(permissions['view_contenttype'])
                    g_reviewer.permissions.add(permissions['view_bughunter'])
                    g_reviewer.permissions.add(permissions['change_bugreport'])
                    g_reviewer.permissions.add(permissions['view_bugreport'])
                    g_reviewer.permissions.add(permissions['delete_bugreport'])
                    g_reviewer.permissions.add(permissions['view_reportstatus'])
                    g_reviewer.permissions.add(permissions['view_staticrules'])
                    g_reviewer.permissions.add(permissions['view_session'])
                except:
                    logging.getLogger("Gerologger").debug("Group Reviewer shall be created successfully. Visit the Admin Site!")

            # INIT THEME
            def init_theme_db():
                if not Personalization.objects.filter(personalize_id=1).exists():
                    THEME = Personalization()
                    THEME.personalize_id    = 1
                    THEME.main_1            = "#171717"
                    THEME.main_2            = "#E8596A"
                    THEME.secondary_1       = "#C82A3D"
                    THEME.secondary_2       = "#FA8997"
                    THEME.secondary_3       = "#FFE0E0"
                    THEME.button_1          = "#48409E"
                    THEME.save()

                    print("[LOG] Init Theme Data success")
                
                else:
                    print("[LOG] Theme Data already exists")

            gerologger_config()
            init_status_db(0, "Not Valid")
            init_status_db(1, "Need to Review")
            init_status_db(2, "In Review")
            init_status_db(3, "Fixing")
            init_status_db(4, "Fixing (Retest)")
            init_status_db(5, "Bounty Calculation")
            init_status_db(6, "Bounty in Process")
            init_status_db(7, "Completed")
            init_group()
            init_rules_db()
            init_cert_db()
            init_mailbox_db()
            init_theme_db()

            logging.getLogger("Gerologger").info("Number of Status         :"+str(ReportStatus.objects.count()))
            logging.getLogger("Gerologger").info("Number of Report         :"+str(BugReport.objects.count()))
            logging.getLogger("Gerologger").info("Number of Bug Hunters    :"+str(BugHunter.objects.count()))


            # RUN GEROMAIL MODULES
            RunGeromailThread(1).start()