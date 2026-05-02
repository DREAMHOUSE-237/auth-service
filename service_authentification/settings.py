"""
Django settings for service_authentification project.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ⚠️ En production, mets la clé secrète dans une variable d’environnement
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'change-me-in-prod')

# ⚠️ DEBUG doit être False en production
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

# ⚠️ Mets ici les IP/domaines autorisés (par ex. Gateway, EC2, localhost)
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
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ✅ CORS : la Gateway gère les credentials
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = False

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

# ✅ Base de données MySQL RDS
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('MYSQL_DB', 'auth_db'),
        'USER': os.environ.get('MYSQL_USER', 'auth_user'),
        'PASSWORD': os.environ.get('MYSQL_PASSWORD', 'htchamba124'),
        'HOST': os.environ.get('MYSQL_HOST', 'dreamhouse237-db.cbc4i248y7jv.eu-north-1.rds.amazonaws.com'),
        'PORT': os.environ.get('MYSQL_PORT', '3306'),
        'OPTIONS': {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        }
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
    # ⚠️ Pas de permission globale pour permettre /api/auth/register
}

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
