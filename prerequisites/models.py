from django.db import models



class MailBox(models.Model):
    mailbox_id = models.IntegerField(default=1)
    email = models.EmailField()
    password = models.TextField(default='')

    def __str__(self):
        return self.email
