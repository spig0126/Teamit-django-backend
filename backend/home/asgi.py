"""
ASGI config for home project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

from chat.routing import websocket_urlpatterns
from firebase_auth.auth_middleware import AuthMiddleware

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "home.settings")

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
     "http": django_asgi_app,
     "websocket": AllowedHostsOriginValidator(
               AuthMiddleware(URLRouter(websocket_urlpatterns))
          ),
})