import os
import django
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import JobApplication

def debug_app_ownership():
    print("--- Debugging Application Ownership ---")
    
    # Check App ID 1 (from screenshot URL)
    try:
        app1 = JobApplication.objects.get(id=1)
        print(f"Application ID: {app1.id}")
        print(f"  Job: {app1.job_posting.title} (Store: {app1.job_posting.template.store.store_name})")
        print(f"  Worker: {app1.worker.username} ({app1.worker.workerprofile.last_name_kanji} {app1.worker.workerprofile.first_name_kanji})")
        print(f"  Status: {app1.status}")
        print(f"  Messages Count: {app1.messages.count()}")
        print("-" * 30)
    except JobApplication.DoesNotExist:
        print("Application ID 1 does not exist.")

    # List applications for all test workers
    print("\n--- All Worker Applications ---")
    test_workers = ['09011112222', '09033334444', '08055556666']
    
    for phone in test_workers:
        apps = JobApplication.objects.filter(worker__username=phone)
        if apps.exists():
            print(f"Worker: {phone}")
            for app in apps:
                print(f"  - App ID: {app.id} | Job: {app.job_posting.title} | Status: {app.status}")
        else:
            print(f"Worker: {phone} has NO applications.")

if __name__ == '__main__':
    debug_app_ownership()
