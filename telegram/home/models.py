from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.auth.models import User
import shortuuid
# Create your models here.


class User(AbstractUser):
    name=models.CharField(max_length=200,null=True)
    email=models.EmailField(unique=True,null=True)
    bio=models.TextField(null=True,blank=True)
    avatar=models.ImageField(null=True,default="avatar.svg")
    phone_number=models.BigIntegerField(null=True,blank=True)

    last_seen=models.DateTimeField(default=timezone.now,null=True)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name="userprofile")  # Ensure this field is defined
    online = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.username} : {self.online}'

# class Room(models.Model):
#     reciver=models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
#     sender=models.OneToOneField(User,on_delete=models.CASCADE,related_name="sender",null=True)

#     def __str__(self):
#         return self.host.username

# class Message(models.Model):
#     sender=models.ForeignKey(User,on_delete=models.CASCADE)
#     reciver=models.ForeignKey(Room,on_delete=models.CASCADE,null=True)
#     body=models.TextField()
#     updated=models.DateTimeField(auto_now=True)
#     created=models.DateTimeField(auto_now_add=True)

#     class Meta:
#         ordering=['-updated','-created']

#     def __str__(self):
#         return self.body[0:50]


class ChatGroup(models.Model):
    group_name=models.CharField(max_length=200,unique=True) #default=shortuuid.uuid
    # users_online=models.ManyToManyField(User,related_name='online_in_groups',blank=True)
    # members=models.ManyToManyField(User,related_name='chat_groups',blank=True)
    # is_private=models.BooleanField(default=False)

    def __str__(self):
        return self.group_name


class GroupMessage(models.Model):
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name='chat_messages',null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.CharField(max_length=300)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.author.username} : {self.body}'
    
    class Meta:
        ordering=['created']


