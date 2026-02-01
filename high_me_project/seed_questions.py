import os
import django
import sys

# Django環境の設定
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from business.models import JobTemplate

def seed_questions():
    # 全てのひな形を取得（あるいは一部）
    templates = JobTemplate.objects.all()
    count = 0
    
    for template in templates:
        # 既に質問がある場合はスキップした方が安全だが、今回は上書き要望と解釈
        # ここでは「質問がない場合」または「強制的に」入れる
        # ユーザー要望的に「いれてほしい」なので、適当なサンプルを入れる
        
        template.question1 = "当日の通勤方法を教えてください（電車・バスなど）"
        template.question2 = "制服のサイズを教えてください（S/M/L）"
        template.question3 = "アレルギーなどがあればお伝えください"
        template.save()
        count += 1
        print(f"Updated template: {template.title}")

    print(f"Successfully updated {count} templates with sample questions.")

if __name__ == '__main__':
    seed_questions()
