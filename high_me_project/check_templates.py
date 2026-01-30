import os
import django
from django.conf import settings
from django.template import loader, engines

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

def check_template(template_name):
    print(f"Checking {template_name}...")
    try:
        t = loader.get_template(template_name)
        print(f"  FOUND: {t.origin.name}")
    except Exception as e:
        print(f"  ERROR: {e}")

templates_to_check = [
    'Searchjobs/index.html',
    'MyPage/index.html',
    'business/Dashboard/dashboard.html',
    'business/Common/base_signup.html',
    'business/Auth/signup.html',
    'administration/login.html',
    'base.html',
]

for t in templates_to_check:
    check_template(t)
