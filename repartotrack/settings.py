import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-repartotrack-dev-key-change-in-production')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']  # Codespaces usa dominios dinámicos

INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'entregas',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'repartotrack.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'repartotrack.wsgi.application'

# Sin base de datos — usamos JSON files como en Flask
DATABASES = {}

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Google Maps API Key — desde .env
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')

# Archivos de datos JSON
DATA_DIR = BASE_DIR
DELIVERIES_FILE = DATA_DIR / 'deliveries.json'
CLIENTS_FILE    = DATA_DIR / 'clients.json'
CONFIG_FILE     = DATA_DIR / 'config.json'
