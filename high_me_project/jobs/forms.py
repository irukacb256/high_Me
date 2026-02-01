from django import forms
from .constants import PREFECTURES

class PrefectureForm(forms.Form):
    pref = forms.MultipleChoiceField(
        choices=[(p, p) for p in PREFECTURES],
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

from business.models import StoreReview

class StoreReviewStep1Form(forms.ModelForm):
    class Meta:
        model = StoreReview
        fields = ['is_time_matched', 'is_content_matched', 'is_want_to_work_again']
        widgets = {
            'is_time_matched': forms.RadioSelect(choices=[(True, 'はい'), (False, 'いいえ')]),
            'is_content_matched': forms.RadioSelect(choices=[(True, 'はい'), (False, 'いいえ')]),
            'is_want_to_work_again': forms.RadioSelect(choices=[(True, 'はい'), (False, 'いいえ')]),
        }
        labels = {
            'is_time_matched': '就業時間は予定どおりでしたか？',
            'is_content_matched': '掲載されていた仕事内容通りでしたか？',
            'is_want_to_work_again': 'またここで働きたいですか？',
        }

class StoreReviewStep2Form(forms.ModelForm):
    class Meta:
        model = StoreReview
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 6, 'placeholder': '皆さんとても親切でした！'}),
        }
        labels = {
            'comment': 'コメント',
        }
