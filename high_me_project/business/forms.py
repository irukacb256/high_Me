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
    
    # 写真用のフィールド
    photos = forms.ImageField(required=False, widget=forms.FileInput) # Temporary widget to avoid ClearableFileInput error if any

    class Meta:
        model = JobTemplate
        exclude = ['store', 'created_at', 'skills', 'other_conditions', 'qualification', 'qualification_type']
        # skills, other_conditions, qualification関連はカスタム処理が必要

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 資格マスター取得
        self.qualifications = QualificationMaster.objects.all().order_by('category', 'name')
        
        # Photos widget override
        self.fields['photos'].widget = MultipleFileInput(attrs={'multiple': True})
    
    def clean(self):
        cleaned_data = super().clean()
        # スキルやその他条件の処理はViewの `request.POST` から取得して `instance` にセットする形になることが多い
        # ModelFormのsave前に commit=False で止めて処理する
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
