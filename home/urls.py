from django.contrib import admin
from django.urls import path, include
from . import views
import home.routing

urlpatterns = [
    path('', views.home, name="home"),
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutPage, name="logout"),
    path('register/', views.registerPage, name="register"),
    path('update_status/', views.update_status, name='update_status'),
    path('private-chat/<username>', views.get_or_create_chatroom, name="start-chat"),
    path('private-chat/room/<chatroom_name>', views.chat_view, name="chatroom"),
    path("delete-message/<int:message_id>/", views.delete_message, name="delete_message"),
    path('message/update/<int:message_id>/', views.update_message, name='update_message'),
    path('upload-media/<chatroom_name>', views.upload_chat_media, name='upload_chat_media'),  # Updated endpoint
]