from django.db import models
from colorfield.fields import ColorField
from django_quill.fields import QuillField



class DashboardsBughunter(models.Model):
    id = models.BigAutoField(primary_key=True)
    hunter_email = models.CharField(max_length=254)
    hunter_username = models.CharField(max_length=30)
    hunter_scores = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'dashboards_bughunter'


class DashboardsStaticrules(models.Model):
    id = models.BigAutoField(primary_key=True)
    rdp = QuillField(db_column='RDP')
    bountyterms = QuillField()
    inscope = QuillField()
    outofscope = QuillField()
    reportguidelines = QuillField()
    faq = QuillField()

    class Meta:
        managed = False
        db_table = 'dashboards_staticrules'


class PrerequisitesMailbox(models.Model):
    id = models.BigAutoField(primary_key=True)
    mailbox_id = models.IntegerField()
    email = models.CharField(max_length=254)
    password = models.TextField()
    mailbox_status = models.IntegerField()
    mailbox_type = models.CharField(max_length=1)
    # mailbox_imap = models.CharField()
    # mailbox_imap_port = models.IntegerField()
    # mailbox_smtp = models.CharField()
    # mailbox_smtp_port = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'prerequisites_mailbox'

class Personalization(models.Model):
    personalize_id = models.IntegerField(primary_key=True)
    main_1      = ColorField()
    main_2      = ColorField()
    secondary_1 = ColorField()
    secondary_2 = ColorField()
    secondary_3 = ColorField()
    button_1    = ColorField()

    class Meta:
        managed = False
        db_table = 'dashboards_personalization'