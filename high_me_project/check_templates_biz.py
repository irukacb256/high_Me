
import os
import django
from django.template import loader

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

def check(name):
    try:
        t = loader.get_template(name)
        print(f"OK: {name}")
    except Exception as e:
        print(f"MISSING: {name} ({e})")

check('business/Common/base_signup.html')
check('business/Dashboard/dashboard.html')
check('business/Auth/signup.html')
check('business/Common/landing.html')
