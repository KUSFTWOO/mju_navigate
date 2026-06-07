from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# SQLite WAL 최적화 (로컬 개발 환경)
if 'default' in DATABASES and DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
    DATABASES['default']['OPTIONS'] = {
        'timeout': 20,
        'init_command': (
            "PRAGMA journal_mode=WAL;"
            "PRAGMA busy_timeout=20000;"
            "PRAGMA foreign_keys=ON;"
            "PRAGMA synchronous=NORMAL;"
            "PRAGMA cache_size=-32000;"
            "PRAGMA temp_store=MEMORY;"
            "PRAGMA mmap_size=134217728;"
        ),
    }

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
