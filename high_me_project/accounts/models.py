from django.db import models
from django.contrib.auth.models import User

class Badge(models.Model):
    """バッジマスター"""
    name = models.CharField("バッジ名", max_length=100)
    icon = models.ImageField("アイコン画像", upload_to='badges/', null=True, blank=True)
    description = models.TextField("説明", blank=True, null=True)

    def __str__(self):
        return self.name

class WorkerProfile(models.Model):
    # Django標準のUserモデルと1対1で紐付け
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='workerprofile')
    
    # 基本情報
    birth_date = models.DateField("生年月日", null=True, blank=True)
    
    # 名前（画像1: 漢字 / 画像2: フリガナ）
    last_name_kanji = models.CharField("姓(漢字)", max_length=50, null=True, blank=True)
    first_name_kanji = models.CharField("名(漢字)", max_length=50, null=True, blank=True)
    last_name_kana = models.CharField("セイ(カナ)", max_length=50, null=True, blank=True)
    first_name_kana = models.CharField("メイ(カナ)", max_length=50, null=True, blank=True)
    
    # 性別（画像3）
    gender = models.CharField("性別", max_length=10, null=True, blank=True)
    
    # 顔写真（画像4）
    face_photo = models.ImageField("顔写真", upload_to='profiles/faces/', null=True, blank=True)
    
    # 住所（画像5）
    postal_code = models.CharField("郵便番号", max_length=7, null=True, blank=True)
    prefecture = models.CharField("都道府県", max_length=20, null=True, blank=True)
    city = models.CharField("市区町村", max_length=100, null=True, blank=True)
    address_line = models.CharField("番地", max_length=100, null=True, blank=True)
    building = models.CharField("建物名・部屋番号", max_length=100, null=True, blank=True)
    
    # 働き方（画像6）
    work_style = models.CharField("アルバイトの働き方", max_length=100, null=True, blank=True)
    career_interest = models.CharField("正社員への興味", max_length=100, null=True, blank=True)
    
    # 希望エリア（画像7: 都道府県選択をカンマ区切りで保存）
    target_prefectures = models.TextField("希望都道府県", null=True, blank=True)

    # 状態管理
    is_setup_completed = models.BooleanField("セットアップ完了", default=False)
    is_identity_verified = models.BooleanField("本人確認済み", default=False)

    def __str__(self):
        return f"{self.user.username} のプロフィール"

class WorkerBadge(models.Model):
    """ワーカーごとのバッジ獲得状況"""
    worker = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    certified_count = models.IntegerField("認定回数", default=0)
    certified_store_count = models.IntegerField("認定店舗数", default=0)
    is_obtained = models.BooleanField("獲得済み", default=False)

    class Meta:
        unique_together = ('worker', 'badge')

    def __str__(self):
        return f"{self.worker.user.username} - {self.badge.name}"