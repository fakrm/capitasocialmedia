from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Post, Profile
from .models import Message
from .models import Comment

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class UserLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

#not all fields are required for profile update
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_pic', 'private_account']



class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'description', 'file', 'post_type']
      



class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Type your message...', 'class': 'w-full p-2 border rounded'})
        }

class PostForm(forms.ModelForm):
    
    
    class Meta:
        model = Post
        fields = ['title', 'description', 'post_type', 'file']        





   