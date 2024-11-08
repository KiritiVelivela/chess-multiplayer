from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib.auth.models import User

@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    # Set a 'logged_in' field to True when the user logs in
    user.userstatus.is_logged_in = True
    user.userstatus.save()

@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    # Set a 'logged_in' field to False when the user logs out
    user.userstatus.is_logged_in = False
    user.userstatus.save()