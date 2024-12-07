from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/game/(?P<game_id>\d+)/$', consumers.GameConsumer.as_asgi()),
    path("ws/home/", consumers.HomeConsumer.as_asgi()),
]