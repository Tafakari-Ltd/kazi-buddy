from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/thread/(?P<thread_id>[0-9a-f-]+)/$', consumers.ChatConsumer.as_asgi()),
]