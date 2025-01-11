from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/conversation/(?P<pk>\d+)/$', consumers.ChatConsumer.as_asgi()),
]