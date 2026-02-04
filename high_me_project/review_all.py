
import os
import django
import sys

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import JobApplication, StoreReview, WorkerReview
from accounts.models import WorkerProfile

def review_all_jobs():
    print("Auto-reviewing all completed jobs as GOOD...")
    apps = JobApplication.objects.filter(status='完了')
    
    count = 0
    for app in apps:
        # Check if WorkerReview exists (Store -> Worker)
        # Assuming WorkerReview model has 'job_application' field? 
        # Let's check model definition. Reference says WorkerReview (Store -> Worker).
        # Usually reviewing the worker.
        
        # Check if review exists
        exists = WorkerReview.objects.filter(worker=app.worker, store=app.job_posting.template.store).exists() 
        # Ideally linked to application 
        
        if not exists:
            WorkerReview.objects.create(
                job_application=app,
                worker=app.worker,
                store=app.job_posting.template.store,
                review_type='good',
                message='Auto-generated review for debug.',
                skills=['元気な挨拶', 'テキパキ']
            )
            print(f"Created Good review for {app.worker.username} at {app.job_posting.template.store.store_name}")
            count += 1
            
    print(f"Created {count} reviews.")

if __name__ == '__main__':
    review_all_jobs()
