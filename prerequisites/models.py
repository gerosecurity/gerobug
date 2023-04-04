from django.db import models



class MailBox(models.Model):
    mailbox_id = models.IntegerField(default=1)
    email = models.EmailField()
    password = models.TextField(default='')
    mailbox_status = models.IntegerField(default=0)

    def __str__(self):
        return self.email

class Webhook(models.Model):
    webhook_service = models.TextField(default='')
    webhook_handle = models.TextField(default='')

    def __str__(self):
        return self.webhook_service