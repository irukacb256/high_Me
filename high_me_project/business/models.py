# business/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# --- 以前作成したモデル ---
class BusinessProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField("会社名", max_length=100)
    business_type = models.CharField("事業形態", max_length=50)
    is_verified = models.BooleanField("本人確認済み", default=False)
    verification_document = models.FileField("確認書類", upload_to='docs/', null=True, blank=True)

class Store(models.Model):
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE)
    store_name = models.CharField("店舗名", max_length=100)
    post_code = models.CharField("郵便番号", max_length=7)
    prefecture = models.CharField("都道府県", max_length=20)
    city = models.CharField("市区町村名", max_length=100)
    address_line = models.CharField("町域・番地", max_length=100)
    building = models.CharField("建物名など", max_length=100, blank=True)

    def __str__(self):
        return self.store_name

# --- 今回追加するモデル ---
class JobTemplate(models.Model):
    # 同じファイル内にあるので、そのまま Store を指定すればOK
    store = models.ForeignKey(Store, on_delete=models.CASCADE) 
    title = models.CharField("求人タイトル", max_length=200)
    industry = models.CharField("業種", max_length=100)
    occupation = models.CharField("職種", max_length=100)
    work_content = models.TextField("業務内容")
    precautions = models.TextField("注意事項")
    
    # 待遇
    has_unexperienced_welcome = models.BooleanField(default=False)
    has_transportation_allowance = models.BooleanField(default=False)
    has_meal = models.BooleanField(default=False)
    has_hair_color_free = models.BooleanField(default=False)
    
    belongings = models.TextField("持ち物")
    requirements = models.TextField("働くための条件")
    
    # 就業場所
    address = models.CharField("就業場所の住所", max_length=255)
    access = models.TextField("アクセス")
    contact_number = models.CharField("緊急連絡先", max_length=20)
    
    auto_message = models.TextField("自動送信メッセージ")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
# business/models.py (JobPostingモデルを以下のように調整)

class JobPosting(models.Model):
    template = models.ForeignKey(JobTemplate, on_delete=models.CASCADE)
    work_date = models.DateField("勤務日")
    start_time = models.TimeField("開始時間")
    end_time = models.TimeField("終了時間")
    title = models.CharField("求人タイトル", max_length=200)
    
    # ★ ここに work_content を追加
    work_content = models.TextField("業務内容", blank=True, null=True)
    
    # 時給・交通費（以前追加したもの）
    hourly_wage = models.IntegerField("時給", default=1100)
    transportation_fee = models.IntegerField("交通費", default=500)
    
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_payment(self):
        return (self.hourly_wage * 5) + self.transportation_fee

    def __str__(self):
        return self.title
    
    @property
    def is_expired(self):
        """現在時刻が開始時刻（締切）を過ぎているか判定"""
        now = timezone.now()
        # 日付と時間を結合して比較
        job_deadline = timezone.make_aware(
            timezone.datetime.combine(self.work_date, self.start_time)
        )
        return now > job_deadline