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
from rest_framework.views import APIView

from django.views.generic import TemplateView

class MessagingView(TemplateView):
    template_name = 'messaging/messaging.html'

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


class ThreadDetailView(generics.ListAPIView):  # Changed from ListCreateAPIView to ListAPIView
    pagination_class = MessagePagination
    serializer_class = MessageSerializer  # Changed to MessageSerializer since we're listing messages
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        thread_id = self.kwargs.get('thread_id')
        user = self.request.user

        if not thread_id:
            # This should never happen due to URL routing, but keeping for safety
            return Message.objects.none()
        
        # Verify user is in thread
        try:
            thread = MessageThread.objects.get(
                Q(id=thread_id) & (Q(participant_1=user) | Q(participant_2=user))
            )
        except MessageThread.DoesNotExist:
            return Message.objects.none()
        
        if user not in [thread.participant_1, thread.participant_2]:
            return Message.objects.none()
        
        # Mark unread messages as read
        unread_messages = Message.objects.filter(
            is_read=False, 
            thread=thread
        ).exclude(sender=user)
        
        if unread_messages.exists():
            unread_messages.update(is_read=True, read_at=timezone.now())

        return thread.messages.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        # Add permission check here since get_queryset can't return Response objects
        thread_id = self.kwargs.get('thread_id')
        user = request.user

        try:
            thread = MessageThread.objects.get(
                Q(id=thread_id) & (Q(participant_1=user) | Q(participant_2=user))
            )
        except MessageThread.DoesNotExist:
            return Response(
                {"error": "Thread not found or you do not have permission to view it."},
                status=status.HTTP_404_NOT_FOUND
            )

        return super().list(request, *args, **kwargs)


class SendMessageView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        recipient = get_object_or_404(CustomUser, id=self.kwargs['user_id'])
        sender = request.user
        message_text = request.data.get('message_text')
        message_type = request.data.get('message_type', 'text')
        attachment_url = request.data.get('attachment_url')

        if not message_text and not attachment_url:
            return Response(
                {"error": "Message text or attachment URL is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Atomic: thread get_or_create + message creation + thread timestamp update
        # must all succeed or fail together to prevent orphaned messages
        with transaction.atomic():
            # Get or create thread (using ordered participants to prevent duplicates)
            p1, p2 = sorted([sender, recipient], key=lambda u: u.id)
            
            thread, created = MessageThread.objects.get_or_create(
                participant_1=p1,
                participant_2=p2,
                defaults={
                    'job': None,
                    'assignment': None, 
                }
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
                message_text=message_text,
                message_type=message_type,
                attachment_url=attachment_url,
            )
            
            # Update thread timestamp
            thread.last_message_at = message.created_at
            thread.save()
        
        # External I/O: WebSocket notification — kept outside transaction
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"thread_{thread.id}",
                {
                    "type": "chat.message",
                    "message": MessageSerializer(message).data
                }
            )
                
        serializer = self.get_serializer(message)
        return Response({
            "message": "Message sent successfully.",
            "data": serializer.data,
            "thread": ThreadSerializer(thread, context={'request': self.request}).data
        }, status=status.HTTP_201_CREATED)
    

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

        # Notify the recipient via WebSocket about the updated message (if channels is configured)
        channel_layer = get_channel_layer()
        if channel_layer:
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
    
class MessageDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        message = self.get_object()

        # Check if user is sender of the message
        if message.sender != request.user:
            raise permissions.PermissionDenied("You do not have permission to delete this message.")

        # Delete the message
        message.delete()

        # Notify the recipient via WebSocket about the deleted message (if channels is configured)
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"thread_{message.thread.id}",
                {
                    "type": "chat.message.delete",
                    "message_id": message.id
                }
            )

        return Response({"detail": "Message deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

    def get_object(self):
        message_id = self.kwargs.get('message_id')
        return get_object_or_404(Message, id=message_id, sender=self.request.user)
    
class DeleteThreadView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        thread_id = self.kwargs.get('thread_id')
        user = request.user

        # Verify user is in thread
        try:
            thread = MessageThread.objects.get(
                Q(id=thread_id) & (Q(participant_1=user) | Q(participant_2=user))
            )
        except MessageThread.DoesNotExist:
            return Response(
                {"error": "Thread not found or you do not have permission to delete it."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Delete the thread
        thread.delete()

        return Response({"detail": "Thread deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


class DeleteAllThreadsByUserView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        user = request.user

        # Delete all threads for the user
        threads = MessageThread.objects.filter(
            Q(participant_1=user) | Q(participant_2=user)
        )
        
        deleted_count = threads.count()
        threads.delete()

        return Response(
            {
                "message": f"{deleted_count} threads deleted successfully."
            },
            status=status.HTTP_204_NO_CONTENT
        )

#delete all messages in a thread
class DeleteAllMessagesInThreadView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        thread_id = self.kwargs.get('thread_id')
        user = request.user

        # Verify user is in thread
        try:
            thread = MessageThread.objects.get(
                Q(id=thread_id) & (Q(participant_1=user) | Q(participant_2=user))
            )
        except MessageThread.DoesNotExist:
            return Response(
                {"error": "Thread not found or you do not have permission to delete messages."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Delete all messages in the thread
        deleted_count = thread.messages.count()
        thread.messages.all().delete()

        return Response(
            {
                "message": f"{deleted_count} messages deleted successfully."
            },
            status=status.HTTP_204_NO_CONTENT
        )
    
class DeleteAllMessagesByUserView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        user = request.user

        # Delete all messages for the user
        deleted_count = Message.objects.filter(sender=user).delete()[0]

        return Response(
            {
                "message": f"{deleted_count} messages deleted successfully."
            },
            status=status.HTTP_204_NO_CONTENT
        )

class StartThreadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        participant_id = request.data.get('participant_id')

        user = CustomUser.objects.filter(id=participant_id).first()
        if not user:
            return Response(
                {"error": "Participant not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        # Your logic to create empty thread
        thread = MessageThread.objects.create(
            participant_1=request.user,
            participant_2=user,
            job=None,  # Assuming job is optional, set to None or provide a valid Job
            assignment=None  # Assuming assignment is optional, set to None or provide a valid Assignment
        )
        return Response({
            'id': thread.id,
            'other_participant': {
                'id': thread.participant_2.id,
                'full_name': thread.participant_2.full_name
            }
        })

#delete everything in all threads
class DeleteAllMessagesView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        # Delete all messages in all threads (no filtering)
        deleted_count = Message.objects.all().delete()[0]

        return Response(
            {
                "message": f"{deleted_count} messages deleted successfully."
            },
            status=status.HTTP_204_NO_CONTENT
        )
    
#delete all threads for testing purposes

class DeleteAllThreadsForTestingView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        user = request.user

        # Delete all threads for the user
        threads = MessageThread.objects.all()  #  delete all threads
        
        deleted_count = threads.count()
        threads.delete()

        return Response(
            {
                "message": f"{deleted_count} threads deleted successfully."
            },
            status=status.HTTP_204_NO_CONTENT
        )
