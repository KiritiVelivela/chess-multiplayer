from django import forms
from django.core import validators
from django.contrib.auth.models import User
 
def validate_location(value):
    if (value[0] != "r") or (not value[1].isdigit()) or \
     (value[2] != "c") or (not value[3].isdigit()):
        raise forms.ValidationError("Use row and column format, e.g. r1c1.")
 
def validate_value(value):
    try:
        int(value)
    except ValueError:
        raise forms.ValidationError("Enter an integer from 1 to 9.")
    if (int(value) < 1 or int(value) > 9):
        raise forms.ValidationError("Enter an integer from 1 to 9.")
 
class SudokuForm(forms.Form):
    location=forms.CharField(min_length=4, max_length=4, strip=True,
        widget=forms.TextInput(attrs={'placeholder':'r1c1','style':'font-size:small'}),
        validators=[validators.MinLengthValidator(4),
        validators.MaxLengthValidator(4),
        validate_location])
    value = forms.CharField(min_length=1, max_length=1, strip=True,
        widget= forms.TextInput(attrs={'placeholder':'1','style':'font-size:small'}),
        validators=[validators.MinLengthValidator(1),
        validators.MaxLengthValidator(1),
        validate_value])
    
class JoinForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))
    email = forms.CharField(widget=forms.TextInput(attrs={'size': '30'}))
    class Meta():
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password')
        help_texts = {
            'username': None
        }

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())
