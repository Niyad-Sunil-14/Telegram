from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.


class User(AbstractUser):
    name=models.CharField(max_length=200,null=True)
    email=models.EmailField(unique=True,null=True)
    bio=models.TextField(null=True)

    avatar=models.ImageField(null=True,default="avatar.svg")

    # last_login=models.DateTimeField(auto_now_add=True,null=True)





