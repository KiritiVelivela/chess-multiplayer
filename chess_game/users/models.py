from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserStatus(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_logged_in = models.BooleanField(default=False)  # New field for login status

# Create UserStatus when a new user is created
@receiver(post_save, sender=User)
def create_user_status(sender, instance, created, **kwargs):
    if created:
        UserStatus.objects.create(user=instance)

# Save UserStatus when the user is saved
@receiver(post_save, sender=User)
def save_user_status(sender, instance, **kwargs):
    instance.userstatus.save()