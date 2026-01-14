"""
WSGI config for photomarket project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'photomarket.settings')
application = get_wsgi_application()
