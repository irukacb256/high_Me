import os
import django
from django.conf import settings
from django.test import RequestFactory
from datetime import date

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from jobs.views import messages
from business.models import JobPosting, JobTemplate, Store, BusinessProfile, JobApplication
from django.contrib.auth.models import User
from accounts.models import WorkerProfile

def verify():
    print("Starting Messages UI Verification...")
    
    # 1. Setup User
    u, _ = User.objects.get_or_create(username='verify_worker_msg')
    u.set_password('password')
    u.save()
    wp, _ = WorkerProfile.objects.get_or_create(user=u)

    # 2. Setup Job Infrastructure 
    biz_user, _ = User.objects.get_or_create(username='biz_owner_msg')
    biz_profile, _ = BusinessProfile.objects.get_or_create(user=biz_user, defaults={'company_name': 'TestBizMsg'})
    store, _ = Store.objects.get_or_create(business=biz_profile, store_name='TestStoreMsg', defaults={'post_code':'000','prefecture':'Tokyo','city':'City','address_line':'1-1'})
    template, _ = JobTemplate.objects.get_or_create(store=store, title='TestJobMsg', defaults={'industry':'Service','occupation':'Staff','work_content':'Work','precautions':'None','address':'Loc','contact_number':'000'})
    
    factory = RequestFactory()

    # --- Case 1: No Data (Empty State) ---
    print("\n[Case 1] No jobs, No applications")
    JobPosting.objects.filter(template=template).delete()
    JobApplication.objects.filter(worker=u).delete()
    
    request = factory.get('/messages/')
    request.user = u
    response = messages(request)
    content = response.content.decode('utf-8')
    
    if '<div class="empty-state">' in content:
        print("SUCCESS: Empty state displayed")
    else:
        print("FAILURE: Empty state NOT displayed")
        
    if '長期バイトの募集が届いています' not in content:
        print("SUCCESS: Long term header NOT displayed")
    else:
        print("FAILURE: Long term header DISPLAYED unexpectedly")

    # --- Case 2: Long-term Job Exists ---
    print("\n[Case 2] Long-term Job Exists")
    JobPosting.objects.create(
        template=template, 
        work_date=date(2030, 1, 1), # Future date
        start_time='09:00', 
        end_time='12:00', 
        title='Long Term Job',
        is_long_term=True, # ★ Flag ON
        is_published=True
    )
    
    response = messages(request)
    content = response.content.decode('utf-8')
    
    if '長期バイトの募集が届いています' in content:
        print("SUCCESS: Long term header displayed")
    else:
        print("FAILURE: Long term header NOT displayed")
        
    if '<div class="empty-state">' not in content:
        print("SUCCESS: Empty state NOT displayed")
    else:
        print("FAILURE: Empty state DISPLAYED unexpectedly")

    # --- Case 3: Job Application Exists (Matches) ---
    print("\n[Case 3] Active Job Application Exists")
    request = factory.get('/messages/')
    request.user = u
    
    JobPosting.objects.all().delete() # Clear jobs
    
    # Create normal job and apply
    jp = JobPosting.objects.create(
        template=template, 
        work_date=date(2030, 1, 1), 
        start_time='09:00', 
        end_time='12:00', 
        title='Normal Job',
        is_long_term=False
    )
    JobApplication.objects.create(job_posting=jp, worker=u, status='確定済み')
    
    response = messages(request)
    content = response.content.decode('utf-8')
    
    if 'マッチング中のやりとり' in content: 
        print("SUCCESS: Matches placeholder displayed")
    else:
        print("FAILURE: Matches placeholder NOT displayed")

    # Check for the empty state DIV specifically
    if '<div class="empty-state">' not in content:
        print("SUCCESS: Empty state NOT displayed")
    else:
        print("FAILURE: Empty state DISPLAYED unexpectedly")
        with open('debug_output.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Saved content to debug_output.html")

    print("\nVerification Finished")

if __name__ == '__main__':
    verify()
