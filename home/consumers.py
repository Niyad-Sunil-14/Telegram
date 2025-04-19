from channels.generic.websocket import WebsocketConsumer
from django.shortcuts import get_object_or_404
from .models import *
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
        async_to_sync(self.channel_layer.group_add)(self.chatroom_name, self.channel_name)
        self.accept()
        if self.user.is_authenticated:
            self.mark_messages_as_seen()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(self.chatroom_name, self.channel_name)

    def receive(self, text_data=None, bytes_data=None):
        if text_data:
            text_data_json = json.loads(text_data)
            if 'type' in text_data_json and text_data_json['type'] == 'ping':
                return
            if 'mark_seen' in text_data_json and text_data_json['mark_seen']:
                self.mark_messages_as_seen()
            elif 'body' in text_data_json:  # Handle text via WebSocket (though we'll rely on HTTP for text+image)
                body = text_data_json.get('body', '')
                message = GroupMessage.objects.create(
                    body=body,
                    author=self.user,
                    group=self.chatroom,
                )
                async_to_sync(self.channel_layer.group_send)(
                    self.chatroom_name,
                    {'type': 'message_handler', 'message_id': message.id}
                )

    def message_handler(self, event):
        message_id = event['message_id']
        message = GroupMessage.objects.get(id=message_id)
        context = {
            'message': message,
            'user': self.user,
            'chatroom_name': self.chatroom_name,
        }
        html = render_to_string("home/partials/chat_message_p.html", context=context)
        self.send(text_data=html)

        for member in self.chatroom.members.all():
            unread_count = self.chatroom.get_unread_count(member)
            last_message = self.chatroom.get_last_message()
            is_seen = last_message.is_seen if last_message and last_message.author == member else None
            
            # Handle display body for photo messages with or without captions
            display_body = message.body
            if message.image:
                if message.body:
                    display_body = f"🖼️: {message.body}"
                else:
                    if member == message.author:
                        display_body = "You sent a photo"
                    else:
                        display_body = "Sent you a photo"
            
            async_to_sync(self.channel_layer.group_send)(
                f"user_{member.id}",
                {
                    'type': 'notify_new_message',
                    'chatroom_name': self.chatroom.group_name,
                    'message_body': display_body,
                    'message_time': message.created.isoformat(),
                    'author_username': message.author.username,
                    'unread_count': unread_count,
                    'is_seen': is_seen,
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
                for member in self.chatroom.members.all():
                    unread_count = self.chatroom.get_unread_count(member)
                    last_message = self.chatroom.get_last_message()
                    is_seen = last_message.is_seen if last_message and last_message.author == member else None
                    async_to_sync(self.channel_layer.group_send)(
                        f"user_{member.id}",
                        {
                            'type': 'notify_unread_update',
                            'chatroom_name': self.chatroom.group_name,
                            'unread_count': unread_count,
                            'is_seen': is_seen,
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
        
        if "join" in text_data_json:
            self.chatroom_name = text_data_json["join"]
            async_to_sync(self.channel_layer.group_add)(
                f"chatroom_{self.chatroom_name}",
                self.channel_name
            )
            return

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

    def edit_message_handler(self, event):
        self.send(text_data=json.dumps({
            "message_id": event["message_id"],
            "body": event["body"]
        }))

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
            'unread_count': event['unread_count'],
        }))

    def notify_unread_update(self, event):
        self.send(text_data=json.dumps({
            'type': 'unread_update',
            'chatroom_name': event['chatroom_name'],
            'unread_count': event['unread_count'],
        }))