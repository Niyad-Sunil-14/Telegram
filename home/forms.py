from . models import User,ChatGroup,GroupMessage
from django import forms
from django.forms import ModelForm
  
class UpdateImg(ModelForm):  
    class Meta:  
        model = User  
        fields = ['avatar']


class EditProfile(ModelForm):
    class Meta:
        model=User
        fields=['username','name','email','phone_number','bio']

class SetName(ModelForm):
    class Meta:
        model=User
        fields=['name']


class ChatmessageCreateForm(ModelForm):
    class Meta:
        model=GroupMessage
        fields=['body']
        widgets={
            'body':forms.TextInput(attrs={'placeholder':'Add message...',
                                          'class':'p-4 text-black',
                                          'maxlength':'300',
                                          'name':'body',
                                          'autofocus':True}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['body'].label = ''  # Remove the label for 'body' field


class EditMessage(ModelForm):
    class Meta:
        model=GroupMessage
        fields=['body']