import os
import django
from django.conf import settings
from django.utils import timezone
from datetime import date as dt_date

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
settings.ALLOWED_HOSTS += ['testserver']

from business.models import JobPosting
from django.contrib.auth.models import User

def inspect_jobs():
    print("--- Job Inspection ---")
    print(f"Timezone: {timezone.get_current_timezone_name()}")
    now = timezone.now()
    print(f"Current UTC time: {now}")
    print(f"Current Local time: {timezone.localtime(now)}")
    
    today_str = now.strftime('%Y-%m-%d')
    local_today = timezone.localtime(now).date()
    
    print(f"UTC Date (used in view currently): {today_str}")
    print(f"Local Date (should be used): {local_today}")
    
    print(f"Total JobPostings: {JobPosting.objects.count()}")
    
    # Check jobs for 'today_str' (The view's logic)
    view_query_cnt = JobPosting.objects.filter(is_published=True, work_date=today_str).count()
    print(f"Jobs for {today_str} (View Logic): {view_query_cnt}")
    
    # Check jobs for 'local_today'
    local_query_cnt = JobPosting.objects.filter(is_published=True, work_date=local_today).count()
    print(f"Jobs for {local_today} (Local Logic): {local_query_cnt}")
    
    # List all published jobs
    published_jobs = JobPosting.objects.filter(is_published=True)
    if published_jobs.exists():
        print("\n--- Published Jobs List ---")
        for job in published_jobs:
            print(f"ID: {job.id}, Title: {job.title}, Date: {job.work_date}, Pref: {job.template.store.prefecture}")
    else:
        print("\nNo published jobs found.")
        
    # Check Verification User
    username = 'verify_refactor' # The user created in previous steps
    if User.objects.filter(username=username).exists():
        u = User.objects.get(username=username)
        if hasattr(u, 'workerprofile'):
            print(f"\nUser '{username}' Prefectures: {u.workerprofile.target_prefectures}")
        else:
            print(f"\nUser '{username}' has no WorkerProfile.")
    else:
        print(f"\nUser '{username}' not found.")

if __name__ == '__main__':
    inspect_jobs()
