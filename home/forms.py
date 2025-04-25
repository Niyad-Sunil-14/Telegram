from .models import User, ChatGroup, GroupMessage
from django import forms
from django.forms import ModelForm

class UpdateImg(ModelForm):  
    class Meta:  
        model = User  
        fields = ['avatar']

class EditProfile(ModelForm):
    class Meta:
        model = User
        fields = ['username', 'name', 'email', 'phone_number', 'bio']

class SetName(ModelForm):
    class Meta:
        model = User
        fields = ['name']

class ChatmessageCreateForm(ModelForm):
    image = forms.ImageField(required=False, widget=forms.FileInput(attrs={'accept': 'image/*', 'id': 'imageInput'}))
    audio = forms.FileField(required=False, widget=forms.FileInput(attrs={'accept': 'audio/*', 'id': 'audioInput'}))
    gif_url = forms.URLField(required=False, widget=forms.HiddenInput(attrs={'id': 'gifInput'}))  # New field for GIFs

    class Meta:
        model = GroupMessage
        fields = ['body', 'image', 'audio', 'gif_url']
        widgets = {
            'body': forms.TextInput(attrs={
                'placeholder': 'Add message...',
                'class': 'p-4 text-black',
                'maxlength': '300',
                'name': 'body',
                'autofocus': True
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['body'].label = ''
        self.fields['image'].label = ''
        self.fields['audio'].label = ''
        self.fields['gif_url'].label = ''

class EditMessage(ModelForm):
    class Meta:
        model = GroupMessage
        fields = ['body']