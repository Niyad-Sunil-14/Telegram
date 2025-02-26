from channels.generic.websocket import WebsocketConsumer
from django.shortcuts import get_object_or_404
from . models import *
import json
from django.template.loader import render_to_string
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async

class ChatroomConsumer(WebsocketConsumer):
    def connect(self):
        self.user=self.scope['user']
        self.chatroom_name=self.scope['url_route']['kwargs']['chatroom_name']
        self.chatroom=get_object_or_404(ChatGroup,group_name=self.chatroom_name)

        async_to_sync(self.channel_layer.group_add)(
            self.chatroom_name,
            self.channel_name
        )
        self.accept()


    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.chatroom_name,
            self.channel_name
        )


    def receive(self, text_data):
        text_data_json=json.loads(text_data)
        body=text_data_json['body']

        message=GroupMessage.objects.create(
            body=body,
            author=self.user,
            group=self.chatroom,
        )
        event={
            'type':'message_handler',
            'message_id':message.id,
        }
        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name,
            event
        )


    def message_handler(self,event):
        message_id=event['message_id']
        message=GroupMessage.objects.get(id=message_id)
        context={
            'message':message,
            'user':self.user,
        }
        html=render_to_string("home/partials/chat_message_p.html",context=context)
        self.send(text_data=html)



class EditMessageConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        self.accept()

    def disconnect(self, close_code):
        pass  # No need to remove from group

    def receive(self, text_data):
        """Handles message editing"""
        text_data_json = json.loads(text_data)
        message_id = text_data_json["message_id"]
        new_body = text_data_json["body"]

        try:
            message = GroupMessage.objects.get(id=message_id, author=self.user)  # Ensure user owns the message
            message.body = new_body
            message.save()

            # Broadcast updated message to all users in the chatroom
            async_to_sync(self.channel_layer.group_send)(
                f"chatroom_{message.group.group_name}",
                {
                    "type": "edit_message_handler",
                    "message_id": message.id,
                    "body": message.body
                }
            )

        except GroupMessage.DoesNotExist:
            self.send(text_data=json.dumps({"error": "Message not found or permission denied"}))

    def edit_message_handler(self, event):
        """Send updated message to all connected users"""
        self.send(text_data=json.dumps({
            "message_id": event["message_id"],
            "body": event["body"]
        }))