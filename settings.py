import os
from pathlib import Path

# ==============================
# BASE_DIR
# ==============================
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================
# SECRET KEY & DEBUG
# ==============================
SECRET_KEY = 'tu_clave_secreta_aqui'
DEBUG = True

ALLOWED_HOSTS = []

# ==============================
# INSTALLED APPS
# ==============================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'hola',  # tu app principal
]

# ==============================
# MIDDLEWARE
# ==============================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ==============================
# ROOT URLS
# ==============================
ROOT_URLCONF = 'Myproyecto.urls'

# ==============================
# TEMPLATES
# ==============================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # tu carpeta de templates
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

# ==============================
# WSGI
# ==============================
WSGI_APPLICATION = 'Myproyecto.wsgi.application'

# ==============================
# DATABASE
# ==============================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ==============================
# AUTH PASSWORD VALIDATION
# ==============================
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

# ==============================
# INTERNATIONALIZATION
# ==============================
LANGUAGE_CODE = 'es-do'
TIME_ZONE = 'America/Santo_Domingo'
USE_I18N = True
USE_TZ = True



# settings.py

# settings.py

# Configuración de correo con Gmail
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Tu cuenta de Gmail
EMAIL_HOST_USER = "tu_correo@gmail.com"
EMAIL_HOST_PASSWORD = "tu_clave_de_aplicacion"

# Dirección que aparecerá en el remitente
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER





# ==============================
#Archivos estáticos (CSS, JS, imágenes)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]  # opcional si tienes carpeta 'static'

# ==============================
# Archivos estáticos (CSS, JS, imágenes)

# ==============================
# MEDIA FILES (opcional)
# ==============================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

# ==============================
# DEFAULT AUTO FIELD
# ==============================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# URL a la que se redirige después del login exitoso
LOGIN_REDIRECT_URL = '/principal/'  # Cambia '/principal/' por la página que quieras

# URL de la página de login (si usas @login_required)
LOGIN_URL = '/login/'  # Cambia '/login/' por la ruta de tu vista de login


CSRF_TRUSTED_ORIGINS = [
    "https://3d1f2aa9-206b-43df-a8af-07445fb6e2a4-00-1k8mu6m2dwss4.worf.replit.dev"
]




