"""
WSGI core for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""

import environ

from django.core.wsgi import get_wsgi_application

environ.Env.read_env(".env")

application = get_wsgi_application()
