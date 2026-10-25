"""
Django settings for service_authentification project.
"""
from datetime import timedelta
from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'authentification',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'service_authentification.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'service_authentification.wsgi.application'

# ──────────────────────────────────────────────────────────────────────────────
# DATABASE
# CONN_MAX_AGE=0  → Django ferme la connexion après chaque requête HTTP.
#                   Indispensable avec RDS qui coupe les connexions idle.
# CONN_HEALTH_CHECKS=True → Django teste la connexion avant de l'utiliser
#                           et en ouvre une nouvelle si elle est morte.
# Ces deux options ensemble empêchent le "Server has gone away" dans le
# consumer RabbitMQ et sous Gunicorn multi-worker.
# ──────────────────────────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=0,
            conn_health_checks=True,
        )
    }
    DATABASES['default']['OPTIONS'] = {
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        'connect_timeout': 10,
        'ssl': {'ca': os.environ.get('DB_SSL_CA', '/certs/global-bundle.pem')},
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('MYSQL_DB', 'auth_db'),
            'USER': os.environ.get('MYSQL_USER', 'auth_user'),
            'PASSWORD': os.environ.get('MYSQL_PASSWORD', ''),
            'HOST': os.environ.get('MYSQL_HOST', 'dreamhouse237-db.cbc4i248y7jv.eu-north-1.rds.amazonaws.com'),
            'PORT': os.environ.get('MYSQL_PORT', '3306'),
            'CONN_MAX_AGE': 0,
            'CONN_HEALTH_CHECKS': True,
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'connect_timeout': 10,
                'ssl': {'ca': os.environ.get('DB_SSL_CA', '/certs/global-bundle.pem')},
            },
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

# Clé dédiée à la signature des JWT, partagée avec proxy-service qui valide
# les tokens à l'entrée du gateway. Repli sur SECRET_KEY tant que le secret
# n'est pas configuré (le changer déconnecte tous les utilisateurs une fois).
# Le frontend ne rafraîchit pas encore le token : l'access token dure une
# journée, la déconnexion pour inactivité (30 min) est gérée côté frontend.
SIMPLE_JWT = {
    'SIGNING_KEY': os.environ.get('JWT_SIGNING_KEY') or SECRET_KEY,
    'ALGORITHM': 'HS256',
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')