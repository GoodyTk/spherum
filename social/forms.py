from django import forms
from .models import Profile, Post, Comment
from django.contrib.auth.forms import UserCreationForm

class ProfileUpdateForm(forms.ModelForm):
    class Meta():
        model = Profile
        fields= ["avatar", "bio", "birth_date"]
        widgets = {'birth_date': forms.DateInput(attrs={'type': 'date'})}

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["content", "image"]
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'О чём вы думаете?'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]