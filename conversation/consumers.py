import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer # type: ignore
from channels.db import database_sync_to_async # type: ignore
# from django.contrib.auth.models import User
# from .models import Conversation, ConversationMessage


# from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['pk']
        self.room_group_name = f'chat_{self.room_name}'

        logger.info(f"Connecting to room {self.room_group_name}")

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        logger.info(f"Connected to room {self.room_group_name}")

    async def disconnect(self, close_code):
        logger.info(f"Disconnecting from room {self.room_group_name}")
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"Disconnected from room {self.room_group_name}")

    async def receive(self, text_data):
        logger.info(f"Received message: {text_data}")
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        username = text_data_json['username']

        # Salvarea mesajului în baza de date
        await self.save_message(self.room_name, message, username)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
            }
        )
        logger.info(f"Sent message to room {self.room_group_name}")

    async def chat_message(self, event):
        message = event['message']
        username = event['username']

        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
        }))
        logger.info(f"Message sent: {message} by {username}")

    #asta am adaugat
    @database_sync_to_async
    def save_message(self, room_name, message, username):
        from django.contrib.auth.models import User
        from .models import Conversation, ConversationMessage

        conversation = Conversation.objects.get(pk=room_name)
        user = User.objects.get(username=username)
        conversation_message = ConversationMessage(
            conversation=conversation,
            content=message,
            created_by=user
        )
        conversation_message.save()