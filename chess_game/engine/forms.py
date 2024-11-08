from django import forms
from .models import Game

# Assuming Game model has a journal_entry field
class JournalForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ['journal_entry']
        widgets = {
            'journal_entry': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
        labels = {
            'journal_entry': 'Game Journal',
        }