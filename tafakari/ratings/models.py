from django.db import models
import uuid
from django.contrib.auth import get_user_model

# Create your models here.
from accounts.models import CustomUser as User

class RatingCategory(models.Model):
    APPLICABLE_TO_CHOICES = [
        ('worker', 'Worker'),
        ('employer', 'Employer'),
        ('both', 'Both'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    applicable_to = models.CharField(max_length=10, choices=APPLICABLE_TO_CHOICES, default='both')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Rating(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment_id = models.UUIDField()
    rater = models.ForeignKey(User, related_name='given_ratings', on_delete=models.CASCADE)
    ratee = models.ForeignKey(User, related_name='received_ratings', on_delete=models.CASCADE)
    overall_rating = models.PositiveSmallIntegerField()
    review_text = models.TextField(blank=True, null=True)
    is_public = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('assignment_id', 'rater', 'ratee')


class RatingDetail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rating = models.ForeignKey(Rating, related_name='details', on_delete=models.CASCADE)
    category = models.ForeignKey(RatingCategory, related_name='details', on_delete=models.CASCADE)
    score = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)