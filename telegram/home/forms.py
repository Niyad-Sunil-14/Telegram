from . models import User  
from django.forms import ModelForm
  
class UpdateImg(ModelForm):  
    class Meta:  
        model = User  
        fields = ['avatar']


# class EditProfile(ModelForm):
#     class Meta:
#         model=User
#         fields=['']