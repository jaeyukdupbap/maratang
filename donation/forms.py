from django import forms
from .models import DonationPool


class DonationPoolForm(forms.ModelForm):
    """기부 이벤트 생성 폼"""
    
    class Meta:
        model = DonationPool
        fields = ['title', 'sponsor', 'start_date', 'end_date', 'goal_points']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '예: 유기동물 보호소 간식 기부'
            }),
            'sponsor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '후원사 이름을 입력하세요'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'goal_points': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '목표 포인트를 입력하세요',
                'min': 1
            }),
        }
        labels = {
            'title': '기부 이벤트 제목',
            'sponsor': '후원사',
            'start_date': '시작일',
            'end_date': '종료일',
            'goal_points': '목표 포인트',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError('종료일은 시작일보다 이후여야 합니다.')
        
        return cleaned_data

