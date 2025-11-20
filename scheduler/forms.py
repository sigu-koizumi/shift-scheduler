from django import forms
from .models import ShiftRequest

class ShiftRequestForm(forms.ModelForm):
    class Meta:
        model = ShiftRequest
        fields = ['staff', 'date', 'start_time', 'end_time', 'availability']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),  # スマホのカレンダーが出るようにする
        }