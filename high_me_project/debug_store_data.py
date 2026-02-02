import os
import django
import sys

# Add project root to path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import Store

print("--- Store Data Inspection ---")
for s in Store.objects.all():
    print(f"ID: {s.id}, Name: {s.store_name}, Industry: '{s.industry}'")
