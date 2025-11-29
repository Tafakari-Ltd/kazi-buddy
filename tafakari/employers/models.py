from django.db import models
from django.utils import timezone
from django.db.models import JSONField
from django.core.exceptions import ValidationError

from accounts.models import CustomUser
import uuid

#

class EmployerProfile(models.Model):
    BUSINESS_TYPES = [
        ('individual', 'Individual'),
        ('small_business', 'Small Business'),
        ('corporation', 'Corporation'),
        ('contractor', 'Contractor'),
    ]

    VERIFICATION_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('under_review', 'Under Review'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPES)
    industry = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    location_text = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    website_url = models.URLField(max_length=500, null=True, blank=True)
    business_registration_number = models.CharField(max_length=100, null=True, blank=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    admin_notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def clean(self):
        if self.user.user_type != "employer":
            raise ValidationError("Only users with user_type='employer' can have an EmployerProfile.")

        from workers.models import WorkerProfile
        if WorkerProfile.objects.filter(user=self.user).exists():
            raise ValidationError("User already has a WorkerProfile.")
        
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


