from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from django.db.models import JSONField
from skills.models import Skill
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

    def calculate_completion(self):
        """Determine the percentage of profile fields that are filled."""
        fields_to_check = [
            self.location,
            self.location_text,
            self.years_experience,
            self.hourly_rate,
            self.availability_schedule,
            self.bio,
        ]
        total = len(fields_to_check)
        filled = sum([1 for field in fields_to_check if field not in [None, '', {}]])
        return int((filled / total) * 100) if total else 0
    
    def clean(self):
        if self.user.user_type != "worker":
            raise ValidationError("Only users with user_type='worker' can have a WorkerProfile.")

        from employers.models import EmployerProfile
        if EmployerProfile.objects.filter(user=self.user).exists():
            raise ValidationError("User already has an EmployerProfile.")


    def save(self, *args, **kwargs):
        self.profile_completion_percentage = self.calculate_completion()
        self.full_clean()
        super().save(*args, **kwargs)

class WorkerSkill(models.Model):
    EXPERIENCE_LEVELS = [
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('expert', 'Expert'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    worker_profile = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVELS, default='intermediate')
    years_experience = models.PositiveIntegerField(default=0)
    is_certified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
            unique_together = ('worker_profile', 'skill')