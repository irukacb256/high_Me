
import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import WorkerProfile
from accounts.services import AchievementService

def fix_grades():
    print("Starting Grade Update...")
    for worker_profile in WorkerProfile.objects.all():
        user = worker_profile.user
        
        # Ensure membership
        if not hasattr(worker_profile, 'membership'):
            continue
            
        old_grade = worker_profile.membership.grade
        
        # Debug Stats
        stats = AchievementService.calculate_stats(worker_profile)
        print(f"Stats for {user.username}: {stats}")
        
        # Calculate stats and update grade
        AchievementService.update_grade(worker_profile)
        
        # Reload to check change
        worker_profile.membership.refresh_from_db()
        new_grade = worker_profile.membership.grade
        
        print(f"User {user.username}: {old_grade} -> {new_grade} (Lv.{worker_profile.membership.level})")

if __name__ == '__main__':
    fix_grades()
