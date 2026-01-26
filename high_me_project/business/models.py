# business/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import WorkerProfile, Badge  # WorkerProfileとBadgeをインポート

# --- 以前作成したモデル ---
class BusinessProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField("会社名", max_length=100)
    business_type = models.CharField("事業形態", max_length=50)
    industry = models.CharField("業種", max_length=50, blank=True, null=True) # 画像1準拠で追加
    is_verified = models.BooleanField("本人確認済み", default=False)
    verification_document = models.FileField("確認書類", upload_to='docs/', null=True, blank=True)
    
    # 所在地 (画像2を基に追加)
    post_code = models.CharField("郵便番号", max_length=7, blank=True, null=True)
    prefecture = models.CharField("都道府県", max_length=20, blank=True, null=True)
    city = models.CharField("市区町村名", max_length=100, blank=True, null=True)
    address_line = models.CharField("町域・番地", max_length=100, blank=True, null=True)
    building = models.CharField("建物名など", max_length=100, blank=True, null=True)

class Store(models.Model):
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE)
    store_name = models.CharField("店舗名", max_length=100)
    industry = models.CharField("業種", max_length=50, blank=True, null=True) # 画像準拠で追加
    post_code = models.CharField("郵便番号", max_length=7)
    prefecture = models.CharField("都道府県", max_length=20)
    city = models.CharField("市区町村名", max_length=100)
    address_line = models.CharField("町域・番地", max_length=100)
    building = models.CharField("建物名など", max_length=100, blank=True)

    @property
    def full_address(self):
        return f"{self.prefecture}{self.city}{self.address_line}{self.building}"

    def __str__(self):
        return self.store_name

class QualificationMaster(models.Model):
    """資格マスタ"""
    name = models.CharField("資格名称", max_length=100)
    category = models.CharField("カテゴリ", max_length=100)

    def __str__(self):
        return f"[{self.category}] {self.name}"

# --- 今回追加するモデル ---
class StoreWorkerGroup(models.Model):
    """店舗がワーカーをグループ分けするためのモデル"""
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    worker = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE)
    GROUP_TYPE_CHOICES = [
        ('favorite', 'お気に入り'),
        ('worked', '稼働経験あり'),
        ('blocked', 'ブロック'),
        ('hall', 'ホール'),        # 画像3にあるグループ例
        # 必要に応じて追加
    ]
    group_type = models.CharField("グループ種別", max_length=50, choices=GROUP_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('store', 'worker', 'group_type')

class StoreWorkerMemo(models.Model):
    """店舗がワーカーに付ける管理用メモ"""
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    worker = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE)
    memo = models.TextField("管理用メモ", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('store', 'worker')

class JobTemplate(models.Model):
    # 同じファイル内にあるので、そのまま Store を指定すればOK
    store = models.ForeignKey(Store, on_delete=models.CASCADE) 
    title = models.CharField("求人タイトル", max_length=200)
    industry = models.CharField("業種", max_length=100)
    occupation = models.CharField("職種", max_length=100)
    work_content = models.TextField("業務内容")
    precautions = models.TextField("注意事項")
    
    # 待遇 (画像2を基に追加)
    has_unexperienced_welcome = models.BooleanField("未経験者歓迎", default=False)
    has_bike_car_commute = models.BooleanField("バイク/車通勤可", default=False)
    has_clothing_free = models.BooleanField("服装自由", default=False)
    has_coupon_get = models.BooleanField("クーポンGET", default=False)
    has_meal = models.BooleanField("まかないあり", default=False)
    has_hair_color_free = models.BooleanField("髪型/カラー自由", default=False)
    has_bike_bicycle_commute = models.BooleanField("バイク/自転車通勤可", default=False)
    has_bicycle_commute = models.BooleanField("自転車通勤可", default=False)
    # 以前のものも残しつつ整理
    has_transportation_allowance = models.BooleanField("交通費支給", default=False)
    
    belongings = models.TextField("持ち物", blank=True, null=True)
    requirements = models.TextField("働くための条件", blank=True, null=True)
    
    # 書類 (画像4)
    manual_pdf = models.FileField("業務に関する書類(PDF)", upload_to='job_manuals/', null=True, blank=True)
    
    # 就業場所 (画像5)
    address = models.CharField("就業場所の住所", max_length=255)
    access = models.TextField("アクセス", blank=True, null=True)
    contact_number = models.CharField("緊急連絡先", max_length=20)
    
    # 受動喫煙防止措置
    SMOKING_CHOICES = [
        ('indoor_no_smoking', '屋内禁煙'),
        ('indoor_smoking_separate', '分煙'),
        ('indoor_smoking_ok', '屋内喫煙可'),
    ]
    smoking_prevention = models.CharField("受動喫煙防止措置", max_length=50, choices=SMOKING_CHOICES, default='indoor_no_smoking')
    has_smoking_area = models.BooleanField("喫煙可能エリアでの作業あり", default=False)
    
    # 資格設定
    requires_qualification = models.BooleanField("資格が必要ですか？", default=False)
    QUAL_CHOICES = [
        ('none', '選択してください'),
        # 運転免許
        ('ordinary_car_license', '普通自動車免許'),
        ('mid_size_car_license', '中型自動車免許'),
        ('large_size_car_license', '大型自動車免許'),
        ('semi_mid_size_car_license', '準中型自動車免許'),
        ('motorcycle_license', '普通自動二輪車免許'),
        ('large_motorcycle_license', '大型自動二輪車免許'),
        ('moped_license', '原付免許'),
        # 専門・技能
        ('forklift', 'フォークリフト'),
        ('hazardous_materials_b4', '危険物取扱者（乙4）'),
        ('food_hygiene_manager', '食品衛生責任者'),
        ('cook', '調理師'),
        # 医療・介護
        ('nursing_care_basics', '介護職員初任者研修'),
        ('registered_seller', '登録販売者'),
        # その他
        ('security_guard_training', '警備員新任教育受講済'),
        ('health_supervisor', '衛生管理者'),
    ]
    qualification_type = models.CharField("資格種別(旧)", max_length=50, choices=QUAL_CHOICES, default='none', blank=True, null=True)
    qualification = models.ForeignKey(QualificationMaster, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="必須資格")
    qualification_notes = models.TextField("資格の補足情報", blank=True, null=True)

    # 申し込み条件 (画像1・2)
    skills = models.TextField("必要なスキル", blank=True, null=True) # カンマ区切りなどで保存
    other_conditions = models.TextField("その他の条件", blank=True, null=True) # 改行区切りなどで保存

    auto_message = models.TextField("自動送信メッセージ", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class JobTemplatePhoto(models.Model):
    """求人ひな形に紐づく写真（最大12枚）"""
    template = models.ForeignKey(JobTemplate, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField("写真", upload_to='job_templates/photos/')
    order = models.PositiveIntegerField("表示順", default=0)

    class Meta:
        ordering = ['order']

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
    
    # 新規追加項目 (詳細表示・マッチング管理用)
    recruitment_count = models.IntegerField("募集人数", default=1)
    break_start = models.TimeField("休憩開始時間", null=True, blank=True)
    break_duration = models.IntegerField("休憩時間(分)", default=0)
    
    # 応募締切日時 (計算して保存)
    application_deadline = models.DateTimeField("応募締切日時", null=True, blank=True)
    
    VISIBILITY_CHOICES = [
        ('public', '一般公開'),
        ('badge', 'バッジ限定'),
        ('group', 'グループ限定'),
        ('first_time', '初回ワーカー限定'),
        ('url', 'URL限定'),
    ]
    visibility = models.CharField("公開範囲", max_length=20, choices=VISIBILITY_CHOICES, default='public')

    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def matched_count(self):
        """確定済みのマッチング人数を返す"""
        return self.applications.filter(status="確定済み").count()

    @property
    def is_old_posting(self):
        """作成から6ヶ月以上経過しているか判定"""
        now = timezone.now()
        six_months_ago = now - timezone.timedelta(days=180)
        return self.created_at < six_months_ago

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
    
class JobApplication(models.Model):
    """ワーカーからの申し込みを管理するモデル"""
    job_posting = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_applications')
    status = models.CharField("状態", max_length=20, default="確定済み")
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # 同じ人が同じ求人に二重に申し込めないように設定
        unique_together = ('job_posting', 'worker')

    def __str__(self):
        return f"{self.worker.last_name} - {self.job_posting.title}"