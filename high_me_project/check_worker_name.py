import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import Store, JobApplication

def check_worker_name():
    store = Store.objects.filter(store_name="海浜幕張カフェ").first()
    if not store:
        print("Store '海浜幕張カフェ' not found.")
        return

    # Find the application for this store (assuming only one from debug script)
    # Actually need to go via JobPosting
    app = JobApplication.objects.filter(job_posting__template__store=store).first()
    
    if app:
        worker = app.worker
        print(f"Application ID: {app.id}")
        print(f"Worker ID: {worker.id}")
        print(f"Username: {worker.username}")
        print(f"Last Name: '{worker.last_name}'")
        print(f"First Name: '{worker.first_name}'")
        print(f"Full Name: '{worker.last_name} {worker.first_name}'")
    else:
        print("No application found for '海浜幕張カフェ'.")

if __name__ == "__main__":
    check_worker_name()
