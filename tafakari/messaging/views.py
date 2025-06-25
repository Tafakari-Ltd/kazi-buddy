from rest_framework import generics, status, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from .models import MessageThread, Message
from .serializers import ThreadSerializer, MessageSerializer
from django.utils import timezone
from accounts.models import CustomUser  
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from rest_framework.pagination import PageNumberPagination

class MessagePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'

class ThreadListView(generics.ListAPIView):

    serializer_class = ThreadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MessageThread.objects.filter(
            Q(participant_1=self.request.user) |
            Q(participant_2=self.request.user)
        ).select_related('participant_1', 'participant_2').prefetch_related('messages').order_by('-last_message_at')

    def get_serializer_context(self):
        return {'request': self.request}


class ThreadDetailView(generics.ListCreateAPIView):
    pagination_class = MessagePagination
    serializer_class = ThreadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        thread_id = self.kwargs.get('thread_id')
        user = self.request.user

        if not thread_id:
            # Return all threads for the user
            return Response(
                'error: thread_id is required',
                 status=status.HTTP_400_BAD_REQUEST
            )
        #verify user is in tread
        try:
            thread = MessageThread.objects.filter(Q(id=thread_id) & (Q(participant_1=user) | Q(participant_2=user))).first()
        except MessageThread.DoesNotExist:
            return MessageThread.objects.none()
        
        #mark unread messages as read
        
        unread_messages = Message.objects.filter(is_read=False,thread=thread).exclude(sender=user)
        
        if unread_messages.exists():
            unread_messages.update(is_read=True, read_at=timezone.now())

        return thread.mesages.oredr_by('-created_at')

class SendMessageView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        recipient = get_object_or_404(CustomUser, id=self.kwargs['user_id'])
        sender = request.user
        
        # Get or create thread (using ordered participants to prevent duplicates)
        p1, p2 = sorted([sender, recipient], key=lambda u: u.id)
        
        thread, created = MessageThread.objects.get_or_create(
            participant_1=p1,
            participant_2=p2,
            job=None,  # Omit job for MVP
            assignment=None  # Omit assignment for MVP
        )
        
        if thread.status == 'blocked':
            return Response(
                {"error": "This conversation is blocked"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create message
        message = Message.objects.create(
            thread=thread,
            sender=sender,
            message_text=request.data.get('message_text'),
            message_type=request.data.get('message_type', 'text'),
            attachment_url=request.data.get('attachment_url')
        )
        
        # Update thread timestamp
        thread.last_message_at = message.created_at
        thread.save()
        # Notify the recipient via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"thread_{thread.id}",
            {
                "type": "chat.message",
                "message": MessageSerializer(message).data
            }
        )
                
        serializer = self.get_serializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class MessageEditView(generics.UpdateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        message = self.get_object()

        # Check if user is sender of the message
        if message.sender != request.user:
            raise permissions.PermissionDenied("You do not have permission to edit this message.")

        # Check if the message is within the allowed edit time window (e.g., 10 minutes)
        time_limit = timezone.now() - timezone.timedelta(minutes=10)
        if message.created_at < time_limit:
            return Response(
                {"error": "You can only edit messages within 10 minutes of sending."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(message, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Notify the recipient via WebSocket about the updated message
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"thread_{message.thread.id}",
            {
                "type": "chat.message.edit",
                "message": MessageSerializer(message).data
            }
        )

        return Response(serializer.data)

    def get_object(self):
        message_id = self.kwargs.get('message_id')
        return get_object_or_404(Message, id=message_id, sender=self.request.user)