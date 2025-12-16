import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from accounts.models import CustomUser
from .models import MessageThread

User = CustomUser

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from accounts.models import CustomUser
from .models import MessageThread

User = CustomUser

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thread_id = self.scope['url_route']['kwargs']['thread_id']
        self.room_group_name = f'thread_{self.thread_id}'

        user = self.scope["user"]
        print(f"[WebSocket Connect] Thread ID: {self.thread_id}")
        print(f"[WebSocket Connect] User: {user} | Authenticated: {not user.is_anonymous}")

        if user.is_anonymous:
            print("[WebSocket Connect] Anonymous user. Closing connection.")
            await self.close()
            return

        has_permission = await self.check_thread_permission(user, self.thread_id)
        print(f"[WebSocket Connect] User has permission: {has_permission}")
        if not has_permission:
            print("[WebSocket Connect] User not authorized for this thread. Closing connection.")
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print("[WebSocket Connect] Connection accepted.")

    async def disconnect(self, close_code):
        print(f"[WebSocket Disconnect] Code: {close_code}")
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    

    async def chat_message(self, event):
        print("[WebSocket Receive] Sending message to frontend:", event['message'])
        message_data = event['message']
        await self.send(text_data=json.dumps({
            "type": "chat.message", 
            "message": message_data
        }))


    @database_sync_to_async
    def check_thread_permission(self, user, thread_id):
        try:
            thread = MessageThread.objects.get(id=thread_id)
            print(f"[Thread Check] Thread exists. Participants: {thread.participant_1}, {thread.participant_2}")
            return user == thread.participant_1 or user == thread.participant_2
        except MessageThread.DoesNotExist:
            print("[Thread Check] Thread does not exist.")
            return False
