import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import WorkerProfile

def check_birthdays():
    print("--- Worker Birth Dates ---")
    profiles = WorkerProfile.objects.all()
    for p in profiles:
        print(f"User: {p.user.username} ({p.last_name_kanji} {p.first_name_kanji}) - Birth Date: {p.birth_date}")

if __name__ == '__main__':
    check_birthdays()
