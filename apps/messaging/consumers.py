import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.channel_name_slug = self.scope['url_route']['kwargs']['channel_name']
        self.room_group_name = f'chat_{self.channel_name_slug}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print(f"WebSocket connected: {self.room_group_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"WebSocket disconnected: {self.room_group_name}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', '')
        user = data.get('user', 'Anonym')
        avatar = data.get('avatar', '?')

        # Broadcast ke semua di room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': user,
                'avatar': avatar,
                'time': timezone.now().strftime('%I:%M %p'),
                'id': data.get('id', ''),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'user': event['user'],
            'avatar': event['avatar'],
            'time': event['time'],
            'id': event['id'],
        }))
