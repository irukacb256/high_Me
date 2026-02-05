import os
import django
import sys

# Djangoのセットアップ
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from business.models import BusinessProfile

def delete_user(phone):
    print(f"Searching for user with ID/Phone: {phone}")
    
    #1. usernameで検索
    user = User.objects.filter(username=phone).first()
    if user:
        user_id = user.id
        user.delete()
        print(f"User with username {phone} (ID: {user_id}) has been deleted.")
        return

    #2. BusinessProfileの電話番号で検索
    biz = BusinessProfile.objects.filter(phone_number=phone).first()
    if biz:
        user = biz.user
        user_id = user.id
        user.delete()
        print(f"User associated with BusinessProfile phone {phone} (ID: {user_id}) has been deleted.")
        return

    print("No user found with that phone number.")

if __name__ == "__main__":
    delete_user('09011112222')
