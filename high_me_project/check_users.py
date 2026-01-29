
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from business.models import BusinessProfile

print('ID | Username | Email | Has BusinessProfile')
print('-------------------------------------------')
for user in User.objects.all():
    has_profile = BusinessProfile.objects.filter(user=user).exists()
    print(f'{user.id} | {user.username} | {user.email} | {has_profile}')
