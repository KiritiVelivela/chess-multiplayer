from django import forms
from journal.models import JournalEntry

class JournalEntryForm(forms.ModelForm):
	description = forms.CharField(widget=forms.TextInput(attrs={'size': '80'}))
	entry = forms.CharField(widget=forms.Textarea(attrs={'style' : "font-family: 'Pacifico', cursive;", 'rows': '8', 'cols':'80'}))
	class Meta():
		model = JournalEntry
		fields = ('description', 'entry')
