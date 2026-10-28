import uuid
from datetime import timedelta
from email.policy import default
from random import choices
from unittest.util import _MAX_LENGTH
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import RegexValidator, MaxValueValidator, MinValueValidator, MinLengthValidator
from django_quill.fields import QuillField
from geromail import gerocalculator
from .rulestemplate import *
from colorfield.fields import ColorField


alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed.')

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)

    def __str__(self):
        return f"{self.user.username} ({self.public_id})"

# Report lifecycle constants shared by the dashboard and the mail pipeline.
# They live here, the bottom layer both import, so the sweep in
# geromail.geroparser.check_auto_agree and the deadline the dashboard shows
# can never drift apart.
BOUNTY_CALC_STATUS = 5      # "Bounty Calculation" (see apps.py init_status_db)
APPEAL_WINDOW_DAYS = 30     # days an unappealed calculation stands before it is accepted


class BugReport(models.Model):
    report_id = models.CharField(max_length=15,primary_key=True,validators=[alphanumeric])
    report_datetime = models.DateTimeField()
    hunter_email = models.EmailField()
    report_reviewer = models.CharField(max_length=50, verbose_name="Report Reviewer")
    report_title = models.CharField(max_length=255, default='NO TITLE')
    report_endpoint = models.CharField(max_length=255, default='NO ENDPOINT')
    report_attack = models.CharField(max_length=255, default='NO ATTACK TYPE')
    report_summary = models.TextField()
    report_severity = models.FloatField(default=0, verbose_name="Report Severity", validators=[MinValueValidator(0.0), MaxValueValidator(10.0)])
    report_severitystring = models.CharField(default="", max_length=255, verbose_name="Severity String", validators=[RegexValidator(regex='(^\(SL:[0-9]\/M:[0-9]\/O:[0-9]\/S:[0-9]\/ED:[0-9]\/EE:[0-9]\/A:[0-9]\/ID:[0-9]\/LC:[0-9]\/LI:[0-9]\/LAV:[0-9]\/LAC:[0-9]\/FD:[0-9]\/RD:[0-9]\/NC:[0-9]\/PV:[0-9]\)$)|(^CVSS:3\.1\/AV:[NALP]\/AC:[LH]\/PR:[NLH]\/UI:[NR]\/S:[UC]\/C:[NLH]\/I:[NLH]\/A:[N|L|H](\/E:[UPFH])?(\/RL:[OTWU])?(\/RC:[URC])?(\/CR:[LMH])?(\/IR:[LMH])?(\/AR:[LMH])?(\/MAV:[NALP])?(\/MAC:[LH])?(\/MPR:[NLH])?(\/MUI:[NR])?(\/MS:[UC])?(\/MC:[NLH])?(\/MI:[NLH])?(\/MA:[NLH])?$)|(^CVSS:4\.0\/AV:[NALP]\/AC:[LH]\/AT:[NP]\/PR:[NLH]\/UI:[NPA]\/VC:[NLH]\/VI:[NLH]\/VA:[NLH]\/SC:[NLH]\/SI:[NLH]\/SA:[NLH].*$)', message='Use OWASP Risk Rating / CVSS 3.1 / CVSS 4.0 Base Vector String')])
    report_severitytype = models.TextField()
    report_status = models.IntegerField(default=1)
    report_duplicate = models.IntegerField(default=0)
    report_permission = models.IntegerField(default=0) # 4 (Update) 2 (Appeal) 1 (NDA) --> UAN --> Similar to RWX System
    report_update = models.IntegerField(default=0)
    # Updates the hunter sent on their own initiative, i.e. without a triager
    # amend request (mail code 701) granting the Update permission bit. Capped
    # at SELF_UPDATE_LIMIT and never reset: report_update cannot serve as the
    # counter because it also numbers the update ids (<report>U1, U2, ...) and
    # counts triager-requested updates, which are deliberately free.
    report_update_self = models.IntegerField(default=0)
    report_appeal = models.IntegerField(default=0)
    report_nda  = models.IntegerField(default=0)
    # When the newest bounty calculation (mail code 702) went to the hunter.
    # Starts the auto-accept clock; re-sending a calculation after an appeal
    # restarts it. Null on reports calculated before this field existed, so
    # those never auto-accept: their hunters were never told about the window.
    report_calc_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
      ordering = ['-report_datetime']
      # order_with_respect_to = "report_datetime"
    
    def __str__(self):
        return self.hunter_email
    
    def get_absolute_url(self):
        return reverse('report_detail', kwargs={'pk':self.report_id})

    @property
    def severity_label(self):
        return gerocalculator.get_severity_label(self.report_severity)

    @property
    def auto_accept_at(self):
        """When silence will be taken as agreement, or None if no clock runs.

        This is the single definition of the deadline: geroparser's sweep acts
        on it and the dashboard displays it, so the board can never promise a
        move the sweep will not make.
        """
        # Bit 2 = appeal still open. Granted only by the calculation email and
        # consumed by an appeal, so holding it means the hunter stayed silent.
        if self.report_status != BOUNTY_CALC_STATUS or not self.report_permission & 2:
            return None
        if self.report_calc_sent_at is None:
            return None
        return self.report_calc_sent_at + timedelta(days=APPEAL_WINDOW_DAYS)


class BugReportUpdate(models.Model):
    update_id = models.CharField(max_length=15,primary_key=True,validators=[alphanumeric])
    report_id = models.CharField(max_length=15)
    update_datetime = models.DateTimeField()
    update_summary = models.TextField()
    update_file = models.IntegerField(default=0)

    def __str__(self):
        return self.update_id
    
    def get_absolute_url(self):
        return reverse('update_detail', kwargs={'pk':self.update_id})


class BugReportAppeal(models.Model):
    appeal_id = models.CharField(max_length=15,primary_key=True,validators=[alphanumeric])
    report_id = models.CharField(max_length=15)
    appeal_datetime = models.DateTimeField()
    appeal_summary = models.TextField()
    appeal_file = models.IntegerField(default=0)

    def __str__(self):
        return self.appeal_id

    def get_absolute_url(self):
        return reverse('appeal_detail', kwargs={'pk':self.appeal_id})

class BugReportNDA(models.Model):
    nda_id = models.CharField(max_length=15,primary_key=True,validators=[alphanumeric])
    report_id = models.CharField(max_length=15)
    nda_datetime = models.DateTimeField()
    nda_summary = models.TextField()
    nda_file = models.IntegerField(default=0)

    def __str__(self):
        return self.nda_id

    def get_absolute_url(self):
        return reverse('nda_detail', kwargs={'pk':self.nda_id})  

class BugHunter(models.Model):
    hunter_email = models.EmailField()
    hunter_username = models.CharField(max_length=50)
    hunter_scores = models.IntegerField()

    def __str__(self):
        return self.hunter_scores


class ReportStatus(models.Model):
    status_id = models.IntegerField(primary_key=True)
    status_name = models.CharField(max_length=30)

    def __str__(self):
        return self.status_name


class StaticRules(models.Model):
    bountyterms = QuillField(blank=False,default=bountyterms_template)
    inscope = QuillField(blank=False,default=inscope_templates)
    outofscope = QuillField(blank=False,default=outofscope_templates)
    RDP = QuillField(blank=False,default=RDP_template)
    reportguidelines = QuillField(blank=False,default=reportguidelines_templates)
    faq = QuillField(blank=False, default=faq_templates)

    def __str__(self):
        return self.RDP


class Watchlist(models.Model):
    email = models.EmailField()
    time = models.IntegerField(default=0)
    counter = models.IntegerField(default=0)

    def __str__(self):
        return self.email


class Blacklist(models.Model):
    email = models.EmailField()
    time = models.IntegerField(default=0)
    informed = models.IntegerField(default=0)

    def __str__(self):
        return self.email
    
class BlacklistRule(models.Model):
    rule_id = models.IntegerField(default=1)
    max_counter = models.IntegerField(default=10)
    buffer_monitor = models.IntegerField(default=60)
    buffer_blacklist = models.IntegerField(default=3600)
    buffer_clean = models.IntegerField(default=86400)

    def __str__(self):
        return self.rule_id
    
class CertificateData(models.Model):
    cert_id = models.IntegerField(default=1)
    officer_name = models.CharField(max_length=30)
    officer_title = models.CharField(max_length=30)

    def __str__(self):
        return self.rule_id
    
class Personalization(models.Model):
    # ROLES: main_1 CANVAS BG, main_2 ACCENT, secondary_1 SURFACE,
    # secondary_2 OVERLAY/HOVER, secondary_3 BORDER, button_1 PRIMARY CTA.
    BRAND_DEFAULTS = {
        'main_1':      '#1A1A1A',
        'main_2':      '#C41230',
        'secondary_1': '#171717',
        'secondary_2': '#2F2F2F',
        'secondary_3': '#3A3A3A',
        'button_1':    '#C41230',
    }

    # THE PALETTE USED BEFORE THE DESIGN SYSTEM LANDED. KEPT SO apps.py CAN
    # RECOGNISE AN UNCUSTOMISED LEGACY INSTALL AND MOVE IT ONTO A PALETTE THE
    # SKIN CAN RENDER LEGIBLY -- secondary_2/3 WERE LIGHT PINKS, AND THE DESIGN
    # SYSTEM PUTS WHITE TEXT ON BOTH.
    LEGACY_DEFAULTS = {
        'main_1':      '#171717',
        'main_2':      '#E8596A',
        'secondary_1': '#C82A3D',
        'secondary_2': '#FA8997',
        'secondary_3': '#FFE0E0',
        'button_1':    '#48409E',
    }

    # SELECTABLE FROM SETTINGS > PERSONALIZATION. ALL ARE DARK-CANVAS THEMES:
    # THE DESIGN SYSTEM HARDCODES LIGHT TEXT. CONSTRAINTS (ENFORCED BY
    # ThemePresetTests): button_1 MUST CARRY WHITE BUTTON TEXT AT >=4.5:1, AND
    # main_2 MUST STAY READABLE AFTER THE --gds-accent-soft MIX
    # (55% ACCENT / 45% WHITE) ON secondary_2.
    THEME_PRESETS = {
        'gero-dark': {
            'name': 'Gero Dark',
            'description': 'The Gero brand default - near-black with crimson.',
            'colors': BRAND_DEFAULTS,
        },
        'gero-classic': {
            'name': 'Gero Classic',
            'description': 'The original Gerobug identity - signature red with purple actions.',
            'colors': {
                'main_1': '#26050C', 'main_2': '#DA0037',
                'secondary_1': '#3A0A16', 'secondary_2': '#4A101E',
                'secondary_3': '#5C1A28', 'button_1': '#48409E',
            },
        },
        'route': {
            'name': 'Route',
            'description': 'Warm plum darks with a pale-aqua highlight and teal actions.',
            'colors': {
                'main_1': '#1A1618', 'main_2': '#9EF5F5',
                'secondary_1': '#241F22', 'secondary_2': '#322A2F',
                'secondary_3': '#453A41', 'button_1': '#0F766E',
            },
        },
        'midnight': {
            'name': 'Midnight',
            'description': 'Deep navy with an electric blue accent.',
            'colors': {
                'main_1': '#10141C', 'main_2': '#3B82F6',
                'secondary_1': '#171C26', 'secondary_2': '#1F2634',
                'secondary_3': '#2A3242', 'button_1': '#2563EB',
            },
        },
        'forest': {
            'name': 'Forest',
            'description': 'Green-tinted darks with an emerald accent.',
            'colors': {
                'main_1': '#0F1512', 'main_2': '#2FA36B',
                'secondary_1': '#16201B', 'secondary_2': '#1D2A23',
                'secondary_3': '#2A3A31', 'button_1': '#1C7F53',
            },
        },
        'royal': {
            'name': 'Royal',
            'description': 'Violet darks with a bright purple accent.',
            'colors': {
                'main_1': '#14101C', 'main_2': '#8B5CF6',
                'secondary_1': '#1B1626', 'secondary_2': '#241D33',
                'secondary_3': '#322A44', 'button_1': '#6D4AE0',
            },
        },
        'graphite': {
            'name': 'Graphite',
            'description': 'Pure monochrome - no accent color at all.',
            'colors': {
                'main_1': '#161616', 'main_2': '#8F8F8F',
                'secondary_1': '#202020', 'secondary_2': '#2A2A2A',
                'secondary_3': '#383838', 'button_1': '#5A5A5A',
            },
        },
    }

    personalize_id = models.IntegerField(default=1)
    company_name = models.CharField(max_length=30, default="GEROBUG")
    main_1      = ColorField(default=BRAND_DEFAULTS['main_1'])
    main_2      = ColorField(default=BRAND_DEFAULTS['main_2'])
    secondary_1 = ColorField(default=BRAND_DEFAULTS['secondary_1'])
    secondary_2 = ColorField(default=BRAND_DEFAULTS['secondary_2'])
    secondary_3 = ColorField(default=BRAND_DEFAULTS['secondary_3'])
    button_1    = ColorField(default=BRAND_DEFAULTS['button_1'])

    @classmethod
    def migrate_legacy_palette(cls):
        # MOVE AN UNCUSTOMISED PRE-DESIGN-SYSTEM INSTALL ONTO THE BRAND
        # DEFAULTS. ONLY AN EXACT MATCH ON EVERY LEGACY COLOR IS MIGRATED, SO
        # AN OPERATOR WHO PICKED THEIR OWN COLORS KEEPS THEM.
        theme = cls.objects.filter(personalize_id=1).first()
        if not theme:
            return False
        current = {f: getattr(theme, f).upper() for f in cls.LEGACY_DEFAULTS}
        if current != {k: v.upper() for k, v in cls.LEGACY_DEFAULTS.items()}:
            return False
        for field, value in cls.BRAND_DEFAULTS.items():
            setattr(theme, field, value)
        theme.save()
        return True

    def __str__(self):
        return self.personalize_id