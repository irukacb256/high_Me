import os
import django
import sys

sys.path.append('c:/Users/y_ootani/Documents/High_Me/high_Me-1/high_me_project')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import Badge

print(f"Badge count: {Badge.objects.count()}")
for b in Badge.objects.all():
    print(f"- {b.name} (id={b.id})")
