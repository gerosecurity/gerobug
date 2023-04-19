from pathlib import Path
from django.core.management.utils import get_random_secret_key
import os



BASE_DIR = Path(__file__).resolve().parent.parent
root_path = str(BASE_DIR).replace("gerobug_dashboard",'')


SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', get_random_secret_key())
DEBUG = False

# READ FROM GEROBUG HOST FILE
f = open(root_path+"gerobug_host", "r")
gerobug_host = f.read()
f.close()

ALLOWED_HOSTS = [gerobug_host] # STATIC INTERNAL IP

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'prerequisites.apps.PrerequisitesConfig',
    'dashboards.apps.DashboardsConfig',
    'geromail.apps.GeromailConfig',
    'ckeditor',
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gerobug.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gerobug.wsgi.application'

# READ FROM DB SECRET FILE
f = open(root_path+"secrets/db_secret.env", "r")
db_secret = f.read()
f.close()

# EXTRACT DB SECRET
db_secret = db_secret.replace("POSTGRES_PASSWORD=",'')
db_secret = db_secret.replace('"','')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'gerobug_db',
        'USER': 'gerobug',
        'PASSWORD': db_secret,
        'HOST': 'db',
        'PORT': '5432',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"
LOGIN_URL="/login/"

USE_L10N = False
DATE_INPUT_FORMATS = ['%d/%m/%Y']
USE_TZ = True


# EMAIL
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True    # mandatory
EMAIL_PORT = 587        # 465 doesn't work
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""

SESSION_COOKIE_HTTPONLY = True


# MEDIA
MEDIA_URL = '/report_files/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'report_files')

CKEDITOR_CONFIGS = {
    "default": {
        "removePlugins": "image,link",
        "allowedContent": "p b li u",
    }
}