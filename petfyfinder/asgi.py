import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter # type: ignore
from channels.auth import AuthMiddlewareStack # type: ignore
import conversation.routing
import logging

logger = logging.getLogger(__name__)

# Setează variabila de mediu pentru setările Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petfyfinder.settings')
logger.info(f"DJANGO_SETTINGS_MODULE: {os.environ['DJANGO_SETTINGS_MODULE']}")

# Initializează Django
django.setup()

logger.info("Django initialized")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            conversation.routing.websocket_urlpatterns
        )
    ),
})

logger.info("ASGI application configured")
