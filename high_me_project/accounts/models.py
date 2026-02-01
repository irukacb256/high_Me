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
    occupation = models.CharField("現在の職業", max_length=50, null=True, blank=True) # 所属選択
    work_style = models.CharField("アルバイトの働き方", max_length=100, null=True, blank=True)
    career_interest = models.CharField("正社員への興味", max_length=100, null=True, blank=True)
    
    # 希望エリア（画像7: 都道府県選択をカンマ区切りで保存）
    target_prefectures = models.TextField("希望都道府県", null=True, blank=True)

    # 緊急連絡先
    emergency_phone = models.CharField("緊急連絡先電話番号", max_length=20, null=True, blank=True)
    emergency_relation = models.CharField("緊急連絡先続柄", max_length=50, null=True, blank=True)

    # 状態管理
    is_setup_completed = models.BooleanField("セットアップ完了", default=False)
    is_identity_verified = models.BooleanField("本人確認済み", default=False)
    identity_document1 = models.ImageField("本人確認書類1", upload_to='profiles/identity/', null=True, blank=True)

    # ペナルティ・キャンセル情報 (画像1参照)
    penalty = models.CharField("ペナルティ", max_length=50, null=True, blank=True) # テキスト用？
    penalty_points = models.IntegerField("ペナルティポイント", default=0)
    cancellations = models.IntegerField("キャンセル数", default=0)
    lastminute_cancel = models.IntegerField("直前キャンセル数", default=0)

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

class WorkerBankAccount(models.Model):
    """画像1: ワーカーの振込先口座情報"""
    worker = models.OneToOneField(WorkerProfile, on_delete=models.CASCADE, related_name='bank_account')
    bank_name = models.CharField("銀行名", max_length=100)
    account_type = models.CharField("口座種別", max_length=20, default='普通') # 普通, 当座 など
    branch_name = models.CharField("支店名", max_length=100)
    account_number = models.CharField("口座番号", max_length=20) # 0落ちを防ぐため文字列
    account_holder_name = models.CharField("口座名義", max_length=100)

    def __str__(self):
        return f"{self.bank_name} - {self.worker.user.username}"

class WalletTransaction(models.Model):
    """画像3/5: ウォレット取引履歴"""
    TRANSACTION_TYPES = (
        ('reward', '報酬'),
        ('withdrawal', '出金'),
        ('bonus', 'ボーナス'), # 仮
    )
    
    worker = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE, related_name='wallet_transactions')
    amount = models.IntegerField("金額") # プラスは入金、マイナスは出金
    transaction_type = models.CharField("取引種別", max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField("内容", max_length=200) # 例: "2024/01/26 〇〇店 報酬"
    created_at = models.DateTimeField("日時", auto_now_add=True)

    def __str__(self):
        return f"{self.get_transaction_type_display()}: {self.amount}円 ({self.created_at})"

class Review(models.Model):
    """店舗からのレビュー"""
    worker = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE, related_name='reviews')
    # Storeモデルが明確でないため、一旦店舗名は文字列で保持、将来的にForeignKey
    store_name = models.CharField("店舗名", max_length=100) 
    comment = models.TextField("コメント", blank=True, null=True)
    is_good = models.BooleanField("Good評価", default=True) # Good率計算用
    created_at = models.DateTimeField("作成日", auto_now_add=True)

    def __str__(self):
        return f"{self.store_name} -> {self.worker.user.username}"

class QualificationCategory(models.Model):
    """資格分野マスター"""
    name = models.CharField("分野名", max_length=100)
    display_order = models.IntegerField("表示順", default=0)

    def __str__(self):
        return self.name

class QualificationItem(models.Model):
    """資格名称マスター"""
    category = models.ForeignKey(QualificationCategory, on_delete=models.CASCADE, related_name='items')
    name = models.CharField("資格名", max_length=100)

    def __str__(self):
        return self.name

class WorkerQualification(models.Model):
    """ワーカー保有資格"""
    worker = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE, related_name='qualifications')
    qualification = models.ForeignKey(QualificationItem, on_delete=models.CASCADE)
    # 画像1の wk_qualification (PATH)
    certificate_image = models.ImageField("資格証明書", upload_to='qualifications/')
    created_at = models.DateTimeField("登録日時", auto_now_add=True)

    def __str__(self):
        return f"{self.worker.user.username} - {self.qualification.name}"

class WorkerMembership(models.Model):
    """画像1: メンバーシップレベル・経験値"""
    worker = models.OneToOneField(WorkerProfile, on_delete=models.CASCADE, related_name='membership')
    GRADE_CHOICES = (
        ('ROOKIE', 'ROOKIE'),
        ('REGULAR', 'REGULAR'),
        ('MASTER', 'MASTER'),
    )
    grade = models.CharField("グレード", max_length=20, choices=GRADE_CHOICES, default='ROOKIE')
    level = models.IntegerField("レベル", default=0)
    current_exp = models.IntegerField("現在の経験値", default=0)
    
    # 次のレベルまでの必要経験値などを計算するロジックが必要だが、
    # 一旦View側で定数管理か、ここでメソッド化する。
    # 仮にレベル * 100 + 200 とか。
    
    def __str__(self):
        return f"{self.worker.user.username} - {self.grade} Lv.{self.level}"

class ExpHistory(models.Model):
    """画像2: EXP獲得履歴"""
    worker = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE, related_name='exp_histories')
    amount = models.IntegerField("獲得EXP")
    reason = models.CharField("獲得理由", max_length=100) # "お仕事完了", "入店マナーの確認" 等
    created_at = models.DateTimeField("獲得日時", auto_now_add=True)

    def __str__(self):
        return f"{self.worker.user.username} +{self.amount}EXP ({self.reason})"