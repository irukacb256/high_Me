from django import forms
from .constants import PREFECTURES

class PrefectureForm(forms.Form):
    pref = forms.MultipleChoiceField(
        choices=[(p, p) for p in PREFECTURES],
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
