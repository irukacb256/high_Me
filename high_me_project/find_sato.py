import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from business.models import JobApplication

def find_sato_takeru():
    u = User.objects.filter(last_name='佐藤', first_name='健').first()
    if not u:
        print("User '佐藤健' not found.")
        return

    print(f"User ID: {u.id}")
    print(f"Username: {u.username}")
    
    apps = JobApplication.objects.filter(worker=u)
    print(f"Number of applications: {apps.count()}")
    for app in apps:
        print(f"  - App ID: {app.id}, Job: {app.job_posting.title}, Status: {app.status}")

if __name__ == "__main__":
    find_sato_takeru()
