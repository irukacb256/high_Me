import os
import django
from django.conf import settings
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
settings.ALLOWED_HOSTS += ['testserver']

from business.models import JobPosting, JobTemplate, Store, BusinessProfile
from django.contrib.auth.models import User

def verify_jobs():
    print("--- Verifying Jobs Refactoring ---")
    c = Client()
    
    # 1. Index Page
    print("Testing GET /home/ (IndexView)...")
    response = c.get(reverse('index'))
    if response.status_code == 200:
        print("SUCCESS: Index page loaded")
    else:
        print(f"FAILURE: Index page returned {response.status_code}")

    # 2. Date Filter
    print("Testing GET /home/?date=... (IndexView Filter)...")
    tomorrow = timezone.localdate() + timedelta(days=1)
    response = c.get(reverse('index'), {'date': tomorrow.strftime('%Y-%m-%d')})
    if response.status_code == 200:
        print("SUCCESS: Index page with date filter loaded")
    else:
        print(f"FAILURE: Index page with date filter returned {response.status_code}")

    # 3. Pref Select (GET)
    print("Testing GET /home/location/prefs/ (PrefSelectView)...")
    response = c.get(reverse('pref_select'))
    if response.status_code == 200:
        print("SUCCESS: Pref select page loaded")
    else:
        print(f"FAILURE: Pref select page returned {response.status_code}")

    # 4. Job Detail
    # Need a job
    job = JobPosting.objects.first()
    if job:
        print(f"Testing GET /job/{job.pk}/ (JobDetailView)...")
        response = c.get(reverse('job_detail', kwargs={'pk': job.pk}))
        if response.status_code == 200:
            print("SUCCESS: Job detail page loaded")
        else:
             print(f"FAILURE: Job detail page returned {response.status_code}")
    else:
        print("WARNING: No job to test detail view")

    # 5. Favorites (Login Required)
    print("Testing GET /favorites/ (FavoritesView) - Should redirect...")
    response = c.get(reverse('favorites'))
    if response.status_code == 302:
        print("SUCCESS: Redirected (Login Required)")
    else:
        print(f"FAILURE: Favorites page returned {response.status_code} (Expected 302)")

    # Login and test Favorites
    user, _ = User.objects.get_or_create(username='verify_user')
    user.set_password('password')
    user.save()
    c.force_login(user)
    
    print("Testing GET /favorites/ (FavoritesView) - Logged in...")
    response = c.get(reverse('favorites'))
    if response.status_code == 200:
        print("SUCCESS: Favorites page loaded")
    else:
        print(f"FAILURE: Favorites page returned {response.status_code}")
        
    # 6. Messages
    print("Testing GET /messages/ (MessagesView)...")
    response = c.get(reverse('messages'))
    if response.status_code == 200:
        print("SUCCESS: Messages page loaded")
    else:
        print(f"FAILURE: Messages page returned {response.status_code}")

if __name__ == '__main__':
    verify_jobs()
