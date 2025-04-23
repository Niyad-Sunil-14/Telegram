from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.auth.models import User
import shortuuid

class User(AbstractUser):
    name = models.CharField(max_length=200, null=True)
    email = models.EmailField(unique=True, null=True)
    bio = models.TextField(null=True, blank=True)
    avatar = models.ImageField(null=True, default="avatar.svg")
    phone_number = models.BigIntegerField(null=True, blank=True)
    last_seen = models.DateTimeField(default=timezone.now, null=True)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="userprofile")
    online = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.username} : {self.online}'

class ChatGroup(models.Model):
    group_name = models.CharField(max_length=200, unique=True, default=shortuuid.uuid)
    members = models.ManyToManyField(User, related_name='chat_groups', blank=True)
    is_private = models.BooleanField(default=False)

    def get_last_message(self):
        return self.chat_messages.order_by('-created').first()
    
    def get_unread_count(self, user):
        return self.chat_messages.filter(is_seen=False).exclude(author=user).count()

    def __str__(self):
        return self.group_name

class GroupMessage(models.Model):
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name='chat_messages', null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.CharField(max_length=300, blank=True, null=True)
    image = models.ImageField(upload_to='chat_images/%Y/%m/%d/', blank=True, null=True)
    audio = models.FileField(upload_to='chat_audio/%Y/%m/%d/', blank=True, null=True)  # New field for audio
    created = models.DateTimeField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True, null=True)
    is_seen = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.author.username} : {self.body or self.image or self.audio or "No content"}'

    class Meta:
        ordering = ['created']

