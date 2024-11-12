from django.contrib import admin
from . models import User,UserProfile,GroupMessage,ChatGroup
# Register your models here.

admin.site.register(User)
admin.site.register(UserProfile)
admin.site.register(GroupMessage)
admin.site.register(ChatGroup)