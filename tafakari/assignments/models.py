from django.db import models
import uuid
from jobs.models import Job
from workers.models import WorkerProfile
from employers.models import EmployerProfile
from applications.models import JobApplication

# Create your models here.
class Assignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    worker = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE)
    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE)
    application = models.ForeignKey(JobApplication, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    agreed_rate = models.DecimalField(max_digits=10, decimal_places=2)
    PAYMENT_TYPE_CHOICES = [
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('fixed', 'Fixed'),
    ]
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    estimated_hours = models.IntegerField(blank=True, null=True)
    actual_hours = models.IntegerField(default=0)
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('disputed', 'Disputed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    completion_percentage = models.IntegerField(default=0)
    worker_started_at = models.DateTimeField(blank=True, null=True)
    worker_completed_at = models.DateTimeField(blank=True, null=True)
    employer_approved_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class AssignmentCheckin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    worker = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE)
    CHECKIN_TYPE_CHOICES = [
        ('start', 'Start'),
        ('break', 'Break'),
        ('resume', 'Resume'),
        ('end', 'End'),
    ]
    checkin_type = models.CharField(max_length=10, choices=CHECKIN_TYPE_CHOICES)
    location = models.CharField(max_length=255, blank=True, null=True)
    location_text = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    photo_url = models.URLField(max_length=500, blank=True, null=True)
    checkin_time = models.DateTimeField(auto_now_add=True)

class AssignmentMilestone(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    completion_notes = models.TextField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)