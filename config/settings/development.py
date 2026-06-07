from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
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
        },
    }
}


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
