from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from dashboards.models import UserProfile


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
