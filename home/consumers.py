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
        self.chatroom_name = None
        self.accept()

    def disconnect(self, close_code):
        if self.chatroom_name:
            async_to_sync(self.channel_layer.group_discard)(
                f"chatroom_{self.chatroom_name}",
                self.channel_name
            )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        
        # Handle joining the chatroom group
        if "join" in text_data_json:
            self.chatroom_name = text_data_json["join"]
            async_to_sync(self.channel_layer.group_add)(
                f"chatroom_{self.chatroom_name}",
                self.channel_name
            )
            return

        # Handle message editing
        message_id = text_data_json["message_id"]
        new_body = text_data_json["body"]

        try:
            message = GroupMessage.objects.get(id=message_id, author=self.user)
            message.body = new_body
            message.save()

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
        self.send(text_data=json.dumps({
            "message_id": event["message_id"],
            "body": event["body"]
        }))



    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        
        # Handle joining the chatroom group
        if "join" in text_data_json:
            self.chatroom_name = text_data_json["join"]
            async_to_sync(self.channel_layer.group_add)(
                f"chatroom_{self.chatroom_name}",
                self.channel_name
            )
            return
        
        # Handle message editing
        if "message_id" in text_data_json and "body" in text_data_json:
            message_id = text_data_json["message_id"]
            new_body = text_data_json["body"]
            
            try:
                message = GroupMessage.objects.get(id=message_id, author=self.user)
                message.body = new_body
                message.save()

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
        
        # Handle message deletion - ADD THIS BLOCK
        if "delete_message_id" in text_data_json:
            message_id = text_data_json["delete_message_id"]
            
            try:
                message = GroupMessage.objects.get(id=message_id, author=self.user)
                group_name = message.group.group_name
                message.delete()
                
                async_to_sync(self.channel_layer.group_send)(
                    f"chatroom_{group_name}",
                    {
                        "type": "delete_message_handler",
                        "message_id": message_id
                    }
                )
            except GroupMessage.DoesNotExist:
                self.send(text_data=json.dumps({"error": "Message not found or permission denied"}))

    # Add this method to handle delete message events
    def delete_message_handler(self, event):
        self.send(text_data=json.dumps({
            "delete_message_id": event["message_id"]
        }))