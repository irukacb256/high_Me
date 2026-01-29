import os
import sys
import django
from django.core.management import call_command

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Djangoのセットアップ
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

def generate_fixture():
    output_file = 'fixtures/initial_data.json'
    
    # ディレクトリが存在するか確認
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    print(f"Generating {output_file} with UTF-8 encoding...")
    
    # UTF-8でファイルを書き込む (重要)
    with open(output_file, 'w', encoding='utf-8') as f:
        call_command(
            'dumpdata',
            '--natural-foreign',
            '--natural-primary',
            exclude=['contenttypes', 'auth.Permission', 'sessions', 'admin.LogEntry'],
            indent=4,
            stdout=f
        )
    
    print("Success! You can now run: python manage.py loaddata fixtures/initial_data.json")

if __name__ == '__main__':
    generate_fixture()
