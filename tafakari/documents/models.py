from django.db import models
import uuid
from accounts.models import CustomUser

# Create your models here.
class DocumentType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    is_required = models.BooleanField(default=False)
    APPLICABLE_TO_CHOICES = [
        ('worker', 'Worker'),
        ('employer', 'Employer'),
        ('both', 'Both'),
    ]
    applicable_to = models.CharField(
        max_length=10, choices=APPLICABLE_TO_CHOICES, default='both'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class UserDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="documents")
    document_type = models.ForeignKey(
        DocumentType, on_delete=models.CASCADE, related_name="user_documents"
    )
    file_name = models.CharField(max_length=255)
    file_url = models.URLField(max_length=500)
    file_type = models.CharField(max_length=50, blank=True, null=True)
    file_size = models.IntegerField(blank=True, null=True)
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    verification_status = models.CharField(
        max_length=10, choices=VERIFICATION_STATUS_CHOICES, default='pending'
    )
    admin_notes = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.file_name