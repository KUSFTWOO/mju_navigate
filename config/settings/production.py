import environ
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # noqa: F401, F403

env = environ.Env()

DEBUG = False

# ── ALLOWED_HOSTS ──────────────────────────────────────────────
# Render는 *.onrender.com 도메인을 자동 할당함
_render_host = env('RENDER_EXTERNAL_HOSTNAME', default='')
_extra_hosts  = env.list('DJANGO_ALLOWED_HOSTS', default=[])

ALLOWED_HOSTS = ['localhost', '127.0.0.1']
if _render_host:
    ALLOWED_HOSTS.append(_render_host)
ALLOWED_HOSTS += _extra_hosts

# ── DATABASE ───────────────────────────────────────────────────
DATABASES = {
    'default': env.db('DATABASE_URL')
}

# ── HTTPS / SECURITY ───────────────────────────────────────────
# Render 프록시가 SSL을 처리하므로 앱 서버에서는 리디렉션하지 않음.
# 대신 X-Forwarded-Proto 헤더를 신뢰해 HTTPS 여부를 판단.
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = [
    f'https://{_render_host}',
] + [f'https://{h}' for h in _extra_hosts if h]
X_FRAME_OPTIONS = 'DENY'

# ── SENTRY ─────────────────────────────────────────────────────
# sentry_sdk는 Django 앱이 아니므로 INSTALLED_APPS에 추가하지 않음
_sentry_dsn = env('SENTRY_DSN', default='')
if _sentry_dsn:
    sentry_sdk.init(
        dsn=_sentry_dsn,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )

# ── LOGGING ────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
