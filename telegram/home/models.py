from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.auth.models import User
# Create your models here.


class User(AbstractUser):
    name=models.CharField(max_length=200,null=True)
    email=models.EmailField(unique=True,null=True)
    bio=models.TextField(null=True)
    avatar=models.ImageField(null=True,default="avatar.svg")
    phone_number=models.IntegerField(null=True)

    last_seen=models.DateTimeField(default=timezone.now,null=True)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name="userprofile")  # Ensure this field is defined
    online = models.BooleanField(default=False)




