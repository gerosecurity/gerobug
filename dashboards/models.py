from email.policy import default
from random import choices
from unittest.util import _MAX_LENGTH
from django.db import models
from django.urls import reverse
from django.core.validators import RegexValidator
from ckeditor.fields import RichTextField
from .rulestemplate import *



alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed.')

class BugReport(models.Model):
    report_id = models.CharField(max_length=15,primary_key=True,validators=[alphanumeric])
    report_datetime = models.DateTimeField()
    hunter_email = models.EmailField()
    report_reviewer = models.TextField(default='')
    report_title = models.TextField(default='NO TITLE')
    report_endpoint = models.TextField(default='NO ENDPOINT')
    report_attack = models.TextField(default='NO ATTACK TYPE')
    report_summary = models.TextField()
    report_severity = models.FloatField(default=0)
    report_status = models.IntegerField(default=1)
    report_duplicate = models.IntegerField(default=0)
    report_permission = models.IntegerField(default=0) # 4 (Update) 2 (Appeal) 1 (NDA) --> UAN --> Similar to RWX System
    report_update = models.IntegerField(default=0)
    report_appeal = models.IntegerField(default=0)
    report_nda  = models.IntegerField(default=0)
    
    def __str__(self):
        return self.hunter_email
    
    def get_absolute_url(self):
        return reverse('report_detail', kwargs={'pk':self.report_id})


class BugHunter(models.Model):
    hunter_email = models.EmailField()
    hunter_username = models.CharField(max_length=30)
    hunter_scores = models.IntegerField()

    def __str__(self):
        return self.hunter_scores


class ReportStatus(models.Model):
    status_id = models.IntegerField(primary_key=True)
    status_name = models.CharField(max_length=30)

    def __str__(self):
        return self.status_name


class StaticRules(models.Model):
    RDP = RichTextField(blank=False,default=RDP_template)
    bountyterms = RichTextField(blank=False,default=bountyterms_template)
    inscope = RichTextField(blank=False,default=inscope_templates)
    outofscope = RichTextField(blank=False,default=outofscope_templates)
    reportguidelines = RichTextField(blank=False,default=reportguidelines_templates)
    faq = RichTextField(blank=False, default=faq_templates)

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