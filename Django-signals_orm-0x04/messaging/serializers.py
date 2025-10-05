from rest_framework import serializers
from .models import Message, MessageHistory

class MessageHistorySerializer(serializers.ModelSerializer):
    editor_username = serializers.CharField(source='editor.username', read_only=True)

    class Meta:
        model = MessageHistory
        fields = ('id', 'old_content', 'edited_at', 'editor', 'editor_username')
        read_only_fields = fields


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('id', 'sender', 'receiver', 'content', 'timestamp', 'edited', 'last_edited_at', 'last_edited_by')
        read_only_fields = ('sender', 'timestamp', 'edited', 'last_edited_at', 'last_edited_by')

