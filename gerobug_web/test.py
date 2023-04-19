# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DashboardsBlacklist(models.Model):
    id = models.BigAutoField(primary_key=True)
    email = models.CharField(max_length=254)
    time = models.IntegerField()
    informed = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'dashboards_blacklist'


class DashboardsBughunter(models.Model):
    id = models.BigAutoField(primary_key=True)
    hunter_email = models.CharField(max_length=254)
    hunter_username = models.CharField(max_length=30)
    hunter_scores = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'dashboards_bughunter'


class DashboardsBugreport(models.Model):
    report_id = models.CharField(primary_key=True, max_length=15)
    report_datetime = models.DateTimeField()
    hunter_email = models.CharField(max_length=254)
    report_reviewer = models.CharField(max_length=25)
    report_title = models.CharField(max_length=50)
    report_endpoint = models.CharField(max_length=50)
    report_attack = models.CharField(max_length=50)
    report_summary = models.TextField()
    report_severity = models.FloatField()
    report_severitystring = models.CharField(max_length=95)
    report_status = models.IntegerField()
    report_duplicate = models.IntegerField()
    report_permission = models.IntegerField()
    report_update = models.IntegerField()
    report_appeal = models.IntegerField()
    report_nda = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'dashboards_bugreport'


class DashboardsBugreportappeal(models.Model):
    appeal_id = models.CharField(primary_key=True, max_length=15)
    report_id = models.CharField(max_length=15)
    appeal_datetime = models.DateTimeField()
    appeal_summary = models.TextField()
    appeal_file = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'dashboards_bugreportappeal'


class DashboardsBugreportnda(models.Model):
    nda_id = models.CharField(primary_key=True, max_length=15)
    report_id = models.CharField(max_length=15)
    nda_datetime = models.DateTimeField()
    nda_summary = models.TextField()

    class Meta:
        managed = False
        db_table = 'dashboards_bugreportnda'


class DashboardsBugreportupdate(models.Model):
    update_id = models.CharField(primary_key=True, max_length=15)
    report_id = models.CharField(max_length=15)
    update_datetime = models.DateTimeField()
    update_summary = models.TextField()

    class Meta:
        managed = False
        db_table = 'dashboards_bugreportupdate'


class DashboardsReportstatus(models.Model):
    status_id = models.IntegerField(primary_key=True)
    status_name = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'dashboards_reportstatus'


class DashboardsStaticrules(models.Model):
    id = models.BigAutoField(primary_key=True)
    rdp = models.TextField(db_column='RDP')  # Field name made lowercase.
    bountyterms = models.TextField()
    inscope = models.TextField()
    outofscope = models.TextField()
    reportguidelines = models.TextField()
    faq = models.TextField()

    class Meta:
        managed = False
        db_table = 'dashboards_staticrules'


class DashboardsWatchlist(models.Model):
    id = models.BigAutoField(primary_key=True)
    email = models.CharField(max_length=254)
    time = models.IntegerField()
    counter = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'dashboards_watchlist'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class PrerequisitesMailbox(models.Model):
    id = models.BigAutoField(primary_key=True)
    mailbox_id = models.IntegerField()
    email = models.CharField(max_length=254)
    password = models.TextField()
    mailbox_status = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'prerequisites_mailbox'


class PrerequisitesWebhook(models.Model):
    id = models.BigAutoField(primary_key=True)
    webhook_service = models.TextField()
    webhook_handle = models.TextField()

    class Meta:
        managed = False
        db_table = 'prerequisites_webhook'
