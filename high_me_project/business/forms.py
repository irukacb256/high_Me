from django import forms
from django.contrib.auth.models import User
from .models import JobTemplate, JobPosting, QualificationMaster

class SignupForm(forms.Form):
    email = forms.EmailField(label="メールアドレス")
    consent = forms.BooleanField(label="利用規約等への同意", required=True)
    # p selects user type (biz/worker) - handled by UI, not needed for backend validation in this form
    # If passed efficiently it's just extra data.

class AccountRegisterForm(forms.Form):
    last_name = forms.CharField(label="姓", max_length=150)
    first_name = forms.CharField(label="名", max_length=150)
    password = forms.CharField(label="パスワード", widget=forms.PasswordInput)
    email = forms.EmailField(label="メールアドレス")

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(username=email).exists():
           # 自身が既に登録済みかどうかはView側でセッションチェックしないとわからないが、
           # 新規登録フローなので基本は重複NG
           raise forms.ValidationError("このメールアドレスは既に登録されています。")
        return email

class BusinessRegisterForm(forms.Form):
    business_type = forms.CharField(label="事業形態")
    industry = forms.CharField(label="業種", required=False)
    
    post_code = forms.CharField(label="郵便番号", max_length=7, required=False)
    prefecture = forms.CharField(label="都道府県", max_length=20, required=False)
    city = forms.CharField(label="市区町村名", max_length=100, required=False)
    address_line = forms.CharField(label="町域・番地", max_length=100, required=False)
    building = forms.CharField(label="建物名など", max_length=100, required=False)

class StoreSetupForm(forms.Form):
    store_name = forms.CharField(label="店舗名", max_length=100)
    industry = forms.CharField(label="業種", required=False)
    
    post_code = forms.CharField(label="郵便番号", max_length=7)
    prefecture = forms.CharField(label="都道府県", max_length=20)
    city = forms.CharField(label="市区町村名", max_length=100)
    address_line = forms.CharField(label="町域・番地", max_length=100)
    building = forms.CharField(label="建物名など", max_length=100, required=False)

class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True

class JobTemplateForm(forms.ModelForm):
    # スキルとその他条件はリストで受け取るUIだが、モデルはTextField(改行/カンマ区切り)
    # View側で処理するか、ここでCleanするか。
    # 既存ロジックはViewで `request.POST.getlist` している。
    # ModelFormとしてはTextFieldとして扱うか、MultipleChoiceFieldなどにするか。
    # ここでは既存のHTMLが name="skills" value="..." のチェックボックス等を送ってくると想定し
    # フォームフィールドは定義せず、Viewで `data=request.POST` した後に `clean` メソッド等で処理、あるいはViewで処理。
    # 既存のHTMLフォーム構造を変えない方針でいくなら、View処理が無難だが、
    # CBV移行なので、Formで吸収したい。
    
    qualification_id = forms.CharField(required=False)

    class Meta:
        model = JobTemplate
        exclude = ['store', 'created_at', 'skills', 'other_conditions', 'qualification', 'qualification_type']
        widgets = {
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 資格マスター取得
        self.qualifications = QualificationMaster.objects.all().order_by('category', 'name')
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title:
            raise forms.ValidationError("求人タイトルを入力してください。")
        return title

    def clean_work_content(self):
        content = self.cleaned_data.get('work_content')
        if not content:
            raise forms.ValidationError("業務内容を入力してください。")
        return content

    def clean(self):
        cleaned_data = super().clean()
        requires_qualification = cleaned_data.get('requires_qualification')
        qualification_id = cleaned_data.get('qualification_id')

        if requires_qualification and (not qualification_id or qualification_id == 'none'):
            self.add_error('qualification_id', "資格が必要な場合は、資格種別を選択してください。")

        # 写真のバリデーション (新規作成時または編集時)
        # Note: request.FILES は view から form = Form(..., files=request.FILES) で渡される想定
        photos = self.files.getlist('photos')
        if not photos and not self.instance.pk:
            # 既存の写真があるかチェック（編集時）
            if not self.instance.photos.exists():
                self.add_error(None, "写真を少なくとも1枚アップロードしてください。")

        return cleaned_data

class JobCreateFromTemplateForm(forms.Form):
    work_date = forms.DateField(label="勤務日")
    start_time = forms.TimeField(label="開始時間")
    end_time = forms.TimeField(label="終了時間")
    title = forms.CharField(label="求人タイトル", required=False) # テンプレートから継承するが変更可
    
    wage = forms.IntegerField(label="時給", initial=1100)
    transport = forms.IntegerField(label="交通費", initial=500)
    
    count = forms.IntegerField(label="募集人数", initial=1)
    break_start = forms.TimeField(label="休憩開始時間", required=False)
    break_duration = forms.IntegerField(label="休憩時間(分)", initial=0)
    
    visibility = forms.ChoiceField(choices=JobPosting.VISIBILITY_CHOICES, initial='public')
    
    deadline = forms.CharField(required=False) # '1h', 'day_before' etc.
    auto_message = forms.CharField(widget=forms.Textarea, required=False)
    msg_send = forms.BooleanField(required=False)

class JobPostingVisibilityForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = ['visibility']

class VerifyDocsForm(forms.Form):
    doc_type = forms.ChoiceField(
        label="書類タイプ",
        choices=[
            ('履歴事項全部証明書', '履歴事項全部証明書（法人の場合）'),
            ('開業届', '開業届（個人事業主の場合）'),
            ('運転免許証', '代表者 運転免許証'),
        ]
    )
    document = forms.FileField(label="書類アップロード")

class BizBasicInfoForm(forms.Form):
    last_name = forms.CharField(label="姓", max_length=150)
    first_name = forms.CharField(label="名", max_length=150)
    phone_number = forms.CharField(label="電話番号", max_length=20, required=False)
    email = forms.EmailField(label="メールアドレス")
    password = forms.CharField(label="パスワード", widget=forms.PasswordInput, required=False, help_text="変更する場合のみ入力してください")
