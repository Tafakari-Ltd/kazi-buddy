from rest_framework import serializers
from .models import Message, MessageThread
from accounts.serializers import UserSerializer

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'sender','message_text', 'message_type', 'attachment_url','created_at']
        read_only_fields = ['id', 'sender', 'created_at']

    read_only_fields = ['id', 'sender', 'created_at','is_read', 'read_at']

class ThreadSerializer(serializers.ModelSerializer):
    other_participant = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = MessageThread
        fields = ['id','other_participant', 'last_message', 'last_message_at','unread_count', 'created_at', 'updated_at']

    def get_other_participant(self, obj):
        current_user = self.context['request'].user
        other = obj.participant_1 if obj.participant_2 == current_user else obj.participant_2
        return UserSerializer(other).data
    
    def get_last_message(self, obj):
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            return MessageSerializer(last_message).data
        return None
    
    def get_unread_count(self, obj):
        current_user = self.context['request'].user
        return obj.messages.filter(is_read=False, sender=current_user).count()