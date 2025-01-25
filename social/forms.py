from django import forms
from .models import Profile
from django.contrib.auth.forms import UserCreationForm

class ProfileUpdateForm(forms.ModelForm):
    class Meta():
        model = Profile
        fields= ["avatar", "bio", "birth_date"]
        widgets = {'birth_date': forms.DateInput(attrs={'type': 'date'})}

