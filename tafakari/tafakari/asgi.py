import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tafakari.settings')
django.setup()

from messaging.routing import websocket_urlpatterns
from .middleware import JWTAuthMiddleware  # custom middleware

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(       
        URLRouter(websocket_urlpatterns)
    ),
})
