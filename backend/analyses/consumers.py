import json
from channels.generic.websocket import AsyncWebsocketConsumer

class AnalysisStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.analysis_id = self.scope['url_route']['kwargs']['analysis_id']
        self.group_name = f'analysis_{self.analysis_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        pass

    async def status_update(self, event):
        await self.send(text_data=json.dumps(event['data']))
