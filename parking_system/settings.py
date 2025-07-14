from pathlib import Path
import os
from django.contrib.messages import constants as messages
import dj_database_url

# BASE_DIR
BASE_DIR = Path(__file__).resolve().parent.parent

# Clave secreta
SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY',
    'django-insecure-ur(&_h7gldf8k1&a7d976gt%c7%2a@3(3!v$zk#=_+f10cxd03'
)

# Debug
DEBUG = True

# Hosts y CSRF - Mejorado para Coolify
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '192.168.1.128',
    '192.168.1.128:3001',
    'parqueadero.sufactura.store',
    '*.sufactura.store',
    '*',
]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost',
    'http://127.0.0.1',
    'https://parqueadero.sufactura.store',
    'http://192.168.1.128',
    'http://192.168.1.128:3001',
]

# Seguridad en producción - Ajustado para Coolify
if not DEBUG:
    # SECURE_SSL_REDIRECT = True  # Puedes activarlo si ya usas HTTPS correctamente
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # SESSION_COOKIE_SECURE = True
    # CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
else:
    SECURE_SSL_REDIRECT = False

# Aplicaciones instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'parking.apps.ParkingConfig',
    'crispy_forms',
    'crispy_tailwind',
    'django.contrib.humanize',
    'widget_tweaks',
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # WhiteNoise agregado aquí
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'parking.middleware.TenantMiddleware',  # Middleware para manejar tenants
    'parking.middleware.TenantRequiredMiddleware',  # Middleware para validar acceso a tenant
]

# URLs
ROOT_URLCONF = 'parking_system.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

# WSGI
WSGI_APPLICATION = 'parking_system.wsgi.application'

# Base de datos
DATABASES = {
    'default': dj_database_url.config(
        default="postgres://postgres:s2CJ8wi4dQwA4jP38wrMOKfHPjCyz5fRkGKX7FQ9WaiTLPCsnVxCs0ipe3tAylHq@jc800wgok88ggw4kkcgckgg8:5432/postgres"
    )
}

# Configuración de base de datos SQLite para desarrollo
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }
# Validadores de contraseñas
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Config regional
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_L10N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True
THOUSAND_SEPARATOR = '.'
DECIMAL_SEPARATOR = ','
NUMBER_GROUPING = 3

# Archivos estáticos - Listo para producción
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Archivos multimedia
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Clave por defecto
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Autenticación
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# Sesiones
SESSION_COOKIE_AGE = 1209600  # 2 semanas
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True

# Mensajes (estilo Tailwind)
MESSAGE_TAGS = {
    messages.DEBUG: 'bg-gray-500 text-white p-4 rounded-lg',
    messages.INFO: 'bg-blue-500 text-white p-4 rounded-lg',
    messages.SUCCESS: 'bg-green-500 text-white p-4 rounded-lg',
    messages.WARNING: 'bg-yellow-500 text-white p-4 rounded-lg',
    messages.ERROR: 'bg-red-500 text-white p-4 rounded-lg',
}

# Configuración de crispy
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# Logging para producción
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'parking': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Configuración para Coolify y proxies
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
