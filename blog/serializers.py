from rest_framework import serializers
from .models import ChatSession, ChatMessage

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'text', 'sender', 'timestamp']  

class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)  
    
    class Meta:
        model = ChatSession
        fields = ['id', 'name', 'database_type', 'created_at', 'last_updated', 'messages']