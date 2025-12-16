from django.db import models
from accounts.models import CustomUser
from django.utils import timezone
from jobs.models import Job
from assignments.models import Assignment
import uuid
# Create your models here.

class MessageThread(models.Model):
    id = models.UUIDField(primary_key=True,editable=False,default=uuid.uuid4)
    STAUS_CHOICES = [
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('blocked', 'blocked'),
    ]
    participant_1 = models.ForeignKey(
        CustomUser,
        related_name='participant_1',
        on_delete=models.CASCADE
    )
    participant_2 = models.ForeignKey(
        CustomUser,
        related_name='participant_2',
        on_delete=models.CASCADE
    )
    job = models.ForeignKey(
        Job,
        related_name='job',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    assignment = models.ForeignKey(
        Assignment,
        related_name='assignment',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=10,
        choices=STAUS_CHOICES,
        default='active'
    )
    last_message_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Thread between {self.participant_1.full_name} and {self.participant_2.full_name} on {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
    
    class Meta:
        unique_together = ('participant_1', 'participant_2', 'job')

class Message(models.Model):
    id = models.UUIDField(primary_key=True, editable=False,default=uuid.uuid4)
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('link', 'Link'),
        ('system', 'System'),
        ('other', 'Other'),
    ]
    thread = models.ForeignKey(
        MessageThread,
        related_name='messages',
        on_delete=models.CASCADE
    )
    sender = models.ForeignKey(
        CustomUser,
        related_name='sender',
        on_delete=models.CASCADE
    )
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPE_CHOICES,
        default='text'
    )
    message_text = models.TextField(blank=True, null=True)
    attachment_url = models.URLField(blank=True, null=True,max_length=500)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_system_message = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Message from {self.sender.full_name} in thread {self.thread.id} at {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

