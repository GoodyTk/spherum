from django import forms
from .models import PollComment, Profile, Post, Comment, PublicGroup
from .models import Poll, Choice

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

class PollForm(forms.ModelForm):
    class Meta:
        model = Poll
        fields = ['question']

class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['text']

class PollCommentForm(forms.ModelForm):
    class Meta:
        model = PollComment
        fields = ['content'] 
    
class PublicGroupForm(forms.ModelForm):
    class Meta:
        model = PublicGroup
        fields = ['name', 'description', 'cover_image']