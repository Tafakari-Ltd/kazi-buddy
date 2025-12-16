from django.db import models
import uuid
from workers.models import WorkerProfile
from employers.models import EmployerProfile
from skills.models import Skill
# Create your models here.
class JobCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    icon_url = models.URLField(max_length=500, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Job(models.Model):
    class JobType(models.TextChoices):
        PART_TIME = 'part_time', 'Part Time'
        FULL_TIME = 'full_time', 'Full Time'
        TEMPORARY = 'temporary', 'Temporary'
        CONTRACT = 'contract', 'Contract'

    class UrgencyLevel(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'

    class PaymentType(models.TextChoices):
        HOURLY = 'hourly', 'Hourly'
        DAILY = 'daily', 'Daily'
        WEEKLY = 'weekly', 'Weekly'
        MONTHLY = 'monthly', 'Monthly'
        FIXED = 'fixed', 'Fixed'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        ACTIVE = 'active', 'Active'
        PAUSED = 'paused', 'Paused'
        FILLED = 'filled', 'Filled'
        CANCELLED = 'cancelled', 'Cancelled'
        COMPLETED = 'completed', 'Completed'

    class Visibility(models.TextChoices):
        PUBLIC = 'public', 'Public'
        PRIVATE = 'private', 'Private'
        INVITED_ONLY = 'invited_only', 'Invited Only'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, related_name='jobs')
    category = models.ForeignKey(JobCategory, null=True, on_delete=models.SET_NULL, related_name='jobs')
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255, null=True, blank=True)
    location_text = models.CharField(max_length=255)
    job_type = models.CharField(max_length=20, choices=JobType.choices)
    urgency_level = models.CharField(max_length=10, choices=UrgencyLevel.choices, default=UrgencyLevel.MEDIUM)
    budget_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    budget_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_type = models.CharField(max_length=10, choices=PaymentType.choices)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    estimated_hours = models.IntegerField(null=True, blank=True)
    max_applicants = models.IntegerField(default=10)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    visibility = models.CharField(max_length=20, choices=Visibility.choices, default=Visibility.PUBLIC)
    admin_approved = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    views_count = models.IntegerField(default=0)
    applications_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    filled_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class JobSkill(models.Model):
    class ExperienceLevel(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'
        EXPERT = 'expert', 'Expert'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='job_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE,related_name='skill_jobs')
    is_required = models.BooleanField(default=True)
    experience_level = models.CharField(max_length=20, choices=ExperienceLevel.choices, default=ExperienceLevel.INTERMEDIATE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'skill')
