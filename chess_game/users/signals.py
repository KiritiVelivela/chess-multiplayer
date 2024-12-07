from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from users.models import UserStatus

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

@receiver(post_save, sender=UserStatus)
def update_available_players(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    if instance.is_logged_in:
        async_to_sync(channel_layer.group_send)(
            "home",
            {
                "type": "broadcast_available_players",
                "players": [
                    {"id": player.user.id, "username": player.user.username}
                    for player in UserStatus.objects.filter(is_logged_in=True)
                ],
            }
        )