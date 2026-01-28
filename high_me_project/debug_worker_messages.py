import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from business.models import JobApplication, Message

def debug_messages():
    print("--- Debugging Worker Messages ---")
    try:
        # Worker Sato Takeru
        worker = User.objects.get(username='09011112222')
        print(f"Worker: {worker.username}")
        
        apps = JobApplication.objects.filter(worker=worker)
        print(f"Total Applications: {apps.count()}")
        
        for app in apps:
            print(f"  App ID: {app.id}")
            print(f"  Job: {app.job_posting.title}")
            print(f"  Status: '{app.status}'")
            print(f"  Messages: {app.messages.count()}")
            for msg in app.messages.all():
                print(f"    - From: {msg.sender.username}, Content: {msg.content}")

    except User.DoesNotExist:
        print("Worker user not found.")

if __name__ == '__main__':
    debug_messages()
