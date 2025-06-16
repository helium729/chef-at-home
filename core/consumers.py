import json

from channels.generic.websocket import AsyncWebsocketConsumer


class OrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.family_id = self.scope["url_route"]["kwargs"]["family_id"]
        self.room_group_name = f"orders_{self.family_id}"

        # Check if user is authenticated and belongs to the family
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        # TODO: Add family membership check
        # For now, accept all authenticated users

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        # For now, we don't handle incoming messages
        # This is mainly for receiving order updates
        pass

    # Receive message from room group
    async def order_update(self, event):
        message = event["message"]

        # Send message to WebSocket
        await self.send(text_data=json.dumps({"type": "order_update", "message": message}))
