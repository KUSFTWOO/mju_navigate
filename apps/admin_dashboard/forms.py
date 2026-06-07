from django import forms
from apps.navigation.models import ShuttleSchedule
from apps.academic.models import AcademicEvent


class ShuttleScheduleForm(forms.ModelForm):
    class Meta:
        model = ShuttleSchedule
        fields = ['route', 'departure_time', 'day_type', 'is_active']
        widgets = {
            'route': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
            'departure_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'
            }),
            'day_type': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-4 h-4'}),
        }


class AcademicEventForm(forms.ModelForm):
    class Meta:
        model = AcademicEvent
        fields = ['title', 'start_date', 'end_date', 'description', 'campus', 'event_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg',
                'rows': 3
            }),
            'campus': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
            'event_type': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg'}),
        }
