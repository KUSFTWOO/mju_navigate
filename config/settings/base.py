import os
from pathlib import Path
import environ
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
# 로컬 개발 시 .env 파일이 있으면 읽음.
# Render 등 PaaS 환경에서는 .env 파일 없이 환경변수로 주입되므로 optional 처리.
_env_file = BASE_DIR / '.env'
if _env_file.exists():
    environ.Env.read_env(_env_file)

SECRET_KEY = env('DJANGO_SECRET_KEY', default='django-insecure-dev-key-change-in-production')

# DEBUG 모드: 'RENDER' 환경변수가 있으면 False (운영), 없으면 True (개발)
DEBUG = 'RENDER' not in os.environ

# ALLOWED_HOSTS: Render 자동 감지 및 환경변수로 추가 호스트 허용
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])
if 'RENDER_EXTERNAL_HOSTNAME' in os.environ:
    ALLOWED_HOSTS.append(os.environ['RENDER_EXTERNAL_HOSTNAME'])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 써드파티 앱
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'crispy_forms',
    'crispy_tailwind',
    'django_htmx',

    # 프로젝트 앱
    'apps.accounts.apps.AccountsConfig',
    'apps.navigation.apps.NavigationConfig',
    'apps.academic.apps.AcademicConfig',
    'apps.restaurants.apps.RestaurantsConfig',
    'apps.admin_dashboard.apps.AdminDashboardConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'config.context_processors.kakao_api_keys',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ─ DATABASE ─────────────────────────────────────────────────────
# DATABASE_URL이 있으면 PostgreSQL(운영), 없으면 SQLite(로컬 개발)
if 'DATABASE_URL' in os.environ:
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ['DATABASE_URL'],
            conn_max_age=600,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'

# 운영 환경(DEBUG=False)에서만 STATIC_ROOT와 WhiteNoise 사용
STATICFILES_DIRS = [BASE_DIR / 'static']

if not DEBUG:
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    # CompressedManifestStaticFilesStorage는 파일명에 해시를 붙여 저장하므로
    # 하드코딩된 경로(/static/js/maps.js)로 참조하는 파일이 404 발생.
    # CompressedStaticFilesStorage는 파일명 변경 없이 압축만 하므로 안전함.
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# django-allauth 설정
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_ADAPTER = 'allauth.account.adapter.DefaultAccountAdapter'

LOGIN_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
ACCOUNT_SIGNUP_REDIRECT_URL = '/accounts/profile/'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@mju-navigate.kr')

# django-crispy-forms 설정
CRISPY_ALLOWED_TEMPLATE_PACKS = 'tailwind'
CRISPY_TEMPLATE_PACK = 'tailwind'

# 외부 API 키
KAKAO_API_KEY = env('KAKAO_API_KEY', default='')
KAKAO_JS_KEY = env('KAKAO_JS_KEY', default='')
ODSAY_API_KEY = env('ODSAY_API_KEY', default='')

# 캐시 설정
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'mju-cache',
    }
}

# 로깅 설정
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
