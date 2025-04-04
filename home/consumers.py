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
        self.user = self.scope['user']
        self.chatroom_name = self.scope['url_route']['kwargs']['chatroom_name']
        self.chatroom = get_object_or_404(ChatGroup, group_name=self.chatroom_name)

        async_to_sync(self.channel_layer.group_add)(
            self.chatroom_name,
            self.channel_name
        )
        self.accept()

        if self.user.is_authenticated:
            self.mark_messages_as_seen()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.chatroom_name,
            self.channel_name
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        
        if 'type' in text_data_json and text_data_json['type'] == 'ping':
            return
            
        if 'body' in text_data_json:
            body = text_data_json['body']
            message = GroupMessage.objects.create(
                body=body,
                author=self.user,
                group=self.chatroom,
            )
            async_to_sync(self.channel_layer.group_send)(
                self.chatroom_name,
                {
                    'type': 'message_handler',
                    'message_id': message.id,
                }
            )
        
        elif 'mark_seen' in text_data_json and text_data_json['mark_seen']:
            self.mark_messages_as_seen()

    def message_handler(self, event):
        message_id = event['message_id']
        message = GroupMessage.objects.get(id=message_id)
        context = {
            'message': message,
            'user': self.user,
        }
        html = render_to_string("home/partials/chat_message_p.html", context=context)
        self.send(text_data=html)
        
        # Notify all group members for left panel update
        for member in self.chatroom.members.all():
            async_to_sync(self.channel_layer.group_send)(
                f"user_{member.id}",
                {
                    'type': 'notify_new_message',
                    'chatroom_name': self.chatroom.group_name,
                    'message_body': message.body,
                    'message_time': message.created.isoformat(),
                    'author_username': message.author.username,
                }
            )

        if self.user != message.author:
            self.mark_messages_as_seen()

    def mark_messages_as_seen(self):
        unseen_messages = GroupMessage.objects.filter(
            group=self.chatroom,
            is_seen=False
        ).exclude(author=self.user)

        if unseen_messages.exists():
            message_ids = []
            for message in unseen_messages:
                message.is_seen = True
                message.save()
                message_ids.append(message.id)

            if message_ids:
                async_to_sync(self.channel_layer.group_send)(
                    self.chatroom_name,
                    {
                        'type': 'seen_handler',
                        'message_ids': message_ids,
                    }
                )

    def seen_handler(self, event):
        self.send(text_data=json.dumps({
            'type': 'message_seen',
            'message_ids': event['message_ids']
        }))

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


class UserNotificationConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            self.close()
            return
        
        self.user_group_name = f"user_{self.user.id}"
        async_to_sync(self.channel_layer.group_add)(
            self.user_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            async_to_sync(self.channel_layer.group_discard)(
                self.user_group_name,
                self.channel_name
            )

    def notify_status(self, event):
        self.send(text_data=json.dumps({
            'type': 'status_update',
            'user_id': event['user_id'],
            'username': event['username'],
            'online': event['online']
        }))

    def notify_new_message(self, event):
        self.send(text_data=json.dumps({
            'type': 'new_message',
            'chatroom_name': event['chatroom_name'],
            'message_body': event['message_body'],
            'message_time': event['message_time'],
            'author_username': event['author_username'],
        }))