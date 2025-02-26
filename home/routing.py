from django.urls import path
from . consumers import *
from django.urls import re_path


websocket_urlpatterns=[
    path("ws/chatroom/<chatroom_name>",ChatroomConsumer.as_asgi()),
    re_path(r"ws/edit_message/$", EditMessageConsumer.as_asgi()),  # Separate WebSocket for editing
    

]