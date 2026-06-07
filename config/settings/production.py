import os
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # noqa: F401, F403

# ── CSRF_TRUSTED_ORIGINS ───────────────────────────────────────
# base.py에서 ALLOWED_HOSTS 설정이 완료되었으므로,
# CSRF_TRUSTED_ORIGINS를 HTTPS 도메인으로 구성
_render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')
_extra_hosts = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',') if 'DJANGO_ALLOWED_HOSTS' in os.environ else []

CSRF_TRUSTED_ORIGINS = []
if _render_host:
    CSRF_TRUSTED_ORIGINS.append(f'https://{_render_host}')
CSRF_TRUSTED_ORIGINS += [f'https://{h.strip()}' for h in _extra_hosts if h.strip()]

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
X_FRAME_OPTIONS = 'DENY'

# ── SENTRY ─────────────────────────────────────────────────────
# sentry_sdk는 Django 앱이 아니므로 INSTALLED_APPS에 추가하지 않음
_sentry_dsn = os.environ.get('SENTRY_DSN', '')
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
