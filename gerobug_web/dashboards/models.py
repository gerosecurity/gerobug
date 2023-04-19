from django.db import models



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
    rdp = models.TextField(db_column='RDP')
    bountyterms = models.TextField()
    inscope = models.TextField()
    outofscope = models.TextField()
    reportguidelines = models.TextField()
    faq = models.TextField()

    class Meta:
        managed = False
        db_table = 'dashboards_staticrules'


class PrerequisitesMailbox(models.Model):
    id = models.BigAutoField(primary_key=True)
    mailbox_id = models.IntegerField()
    email = models.CharField(max_length=254)
    password = models.TextField()
    mailbox_status = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'prerequisites_mailbox'