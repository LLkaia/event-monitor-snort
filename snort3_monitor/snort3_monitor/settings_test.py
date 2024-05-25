from .settings import *


DEBUG = False
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "snort",
        "USER": "postgres",
        "PASSWORD": "ilusha052000",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
