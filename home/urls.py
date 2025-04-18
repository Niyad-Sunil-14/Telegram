"""
URL configuration for telegram project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from . import views
import home.routing

urlpatterns = [
    path('',views.home,name="home"),
    path('login/',views.loginPage,name="login"),
    path('logout/',views.logoutPage,name="logout"),
    path('register/',views.registerPage,name="register"),

    path('update_status/', views.update_status, name='update_status'),

    path('private-chat/<username>',views.get_or_create_chatroom,name="start-chat"),
    path('private-chat/room/<chatroom_name>',views.chat_view,name="chatroom"),

    path("delete-message/<int:message_id>/", views.delete_message, name="delete_message"),
    path('message/update/<int:message_id>/', views.update_message, name='update_message'),

    path('upload-image/<chatroom_name>', views.upload_chat_image, name='upload_chat_image'),  # New endpoint
    path('upload-audio/<str:chatroom_name>', views.upload_chat_audio, name='upload_chat_audio'),

]
