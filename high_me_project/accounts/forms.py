from django import forms
from django.contrib.auth.models import User
from .models import WorkerProfile

class SignupForm(forms.Form):
    phone = forms.CharField(max_length=15, label='電話番号')
    password = forms.CharField(widget=forms.PasswordInput, label='パスワード')

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if User.objects.filter(username=phone).exists():
            raise forms.ValidationError('この電話番号は既に登録されています。')
        return phone

class NameForm(forms.Form):
    last_name = forms.CharField(max_length=30, label='姓')
    first_name = forms.CharField(max_length=30, label='名')

class KanaForm(forms.Form):
    last_name_kana = forms.CharField(max_length=30, label='セイ')
    first_name_kana = forms.CharField(max_length=30, label='メイ')

class GenderForm(forms.Form):
    GENDER_CHOICES = [
        ('female', '女性'),
        ('male', '男性'),
        ('other', 'その他'),
    ]
    gender = forms.ChoiceField(choices=GENDER_CHOICES, widget=forms.RadioSelect, label='性別')

class PhotoForm(forms.Form):
    face_photo = forms.ImageField(label='顔写真', required=False)

class AddressForm(forms.Form):
    postal_code = forms.CharField(max_length=8, label='郵便番号')
    prefecture = forms.CharField(max_length=10, label='都道府県', required=False) # JSで自動入力されることが多い
    city = forms.CharField(max_length=50, label='市区町村')
    address_line = forms.CharField(max_length=100, label='番地')
    building = forms.CharField(max_length=100, label='建物名', required=False)

class WorkstyleForm(forms.Form):
    work_style = forms.CharField(label='現在の職業', required=False)
    career_interest = forms.CharField(label='興味のある職種', required=False)

class VerifyDobForm(forms.Form):
    year = forms.IntegerField()
    month = forms.IntegerField()
    day = forms.IntegerField()

class PrefectureSelectForm(forms.Form):
    prefs = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=[]) # Viewでchoicesをセットする想定
