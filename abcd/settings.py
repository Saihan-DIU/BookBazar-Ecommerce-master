import os
from decouple import config

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'pn5lr!@gag21-z985)ph9(il=!j1wun1=%2zwfrldithj+l5va'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Fix for Django 3.2+ auto field warning
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Local apps
    'eco.apps.EcoConfig',
    'users.apps.UsersConfig',
   
    # Third party apps
    'django_countries',
    'crispy_forms',
    'crispy_bootstrap4',
    'mptt',
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

ROOT_URLCONF = 'abcd.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',  # For media files
                'eco.context_processors.cart_count',  # Add this line - Cart context processor
            ],
        },
    },
]

WSGI_APPLICATION = 'abcd.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
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


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Custom User Model
AUTH_USER_MODEL = 'users.CustomUser'

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Crispy Forms
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# Email Configuration (for development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Stripe Configuration (for payments)
STRIPE_PUBLIC_KEY = 'pk_test_51HHON9JPYmkoAsB01yYUI288THzt2kKmjqu8BdzUePai7grGYVZfUKT3l3mezN15lGo4Zh8yHdFx0i4PSGChrwh800wK4Tgtmz'
STRIPE_SECRET_KEY = 'sk_test_51HHON9JPYmkoAsB0R80Mtvq8Bmd7G252UDuO9uCL0zFKKEbtM2RNqJOqXrmmqLEHyfE3CxuqOIMFkoB36t1QX5wM005bBFDEvI'

# Session settings (important for cart functionality)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds

# Security settings for development
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:8000', 'http://localhost:8000']