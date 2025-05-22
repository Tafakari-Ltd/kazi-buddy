from django.db import models
from django.utils import timezone

from django.db.models import JSONField

from accounts.models import CustomUser
import uuid
# Create your models here.
# workers/models.py

class WorkerProfile(models.Model):
    VERIFICATION_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('under_review', 'Under Review'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    location = models.CharField(max_length=255, null=True, blank=True)
    location_text = models.CharField(max_length=255, null=True, blank=True)
    years_experience = models.PositiveIntegerField(null=True, blank=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    availability_schedule = JSONField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    is_available = models.BooleanField(default=True)
    profile_completion_percentage = models.PositiveIntegerField(default=0)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    admin_notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
