import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from business.models import BusinessProfile, Store

def check_biz_user():
    print("--- Checking Business User ---")
    try:
        u = User.objects.get(username='chiba@example.com') # using the email username I set
        print(f"User: {u.username} (id={u.id})")
        
        prof = BusinessProfile.objects.filter(user=u).first()
        if prof:
            print(f"BusinessProfile found: {prof.company_name} (id={prof.id})")
            store = Store.objects.filter(business=prof).first()
            if store:
                print(f"Store found: {store.store_name} (id={store.id})")
            else:
                print("No Store found.")
        else:
            print("NO BusinessProfile found!")
            
    except User.DoesNotExist:
        print("User 'chiba@example.com' not found.")

if __name__ == '__main__':
    check_biz_user()
