import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User

def create_fallback_admin():
    # 1. Check 'iruka'
    try:
        u = User.objects.get(username='iruka')
        print(f"User 'iruka': active={u.is_active}, staff={u.is_staff}, superuser={u.is_superuser}")
        u.set_password('password')
        u.save()
        print("Reset 'iruka' password to 'password' again.")
    except User.DoesNotExist:
        print("User 'iruka' does not exist.")

    # 2. Create 'admin'
    try:
        admin, created = User.objects.get_or_create(username='admin')
        admin.set_password('admin')
        admin.is_staff = True
        admin.is_superuser = True
        admin.is_active = True
        admin.save()
        if created:
            print("Created new superuser 'admin' with password 'admin'.")
        else:
            print("Reset existing user 'admin' password to 'admin' and ensured superuser status.")
            
    except Exception as e:
        print(f"Error creating admin: {e}")

if __name__ == '__main__':
    create_fallback_admin()
