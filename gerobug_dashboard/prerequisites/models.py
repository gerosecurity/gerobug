from django.db import models



class MailBox(models.Model):
    mailbox_id = models.IntegerField(default=1)
    email = models.EmailField()
    password = models.TextField(default='')
    mailbox_status = models.IntegerField(default=0)
    mailbox_type = models.CharField(default='1', max_length=1)
    mailbox_imap = models.CharField(default='imap.gmail.com', max_length=100)
    mailbox_imap_port = models.IntegerField(default=993)
    mailbox_smtp = models.CharField(default='smtp.gmail.com', max_length=100)
    mailbox_smtp_port = models.IntegerField(default=465)

    def __str__(self):
        return self.email

class Webhook(models.Model):
    webhook_service = models.TextField(default='')
    webhook_handle = models.TextField(default='')

    def __str__(self):
        return self.webhook_service