from django.db import models
import uuid
from accounts.models import CustomUser

# Create your models here.
class SkillCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    icon_url = models.URLField(max_length=500, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        CustomUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_categories_skillcategory'
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        CustomUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='updated_categories_skillcategory'
    )

    def __str__(self):
        return self.name
    
class Skill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(SkillCategory, null=True, on_delete=models.SET_NULL, related_name='skills')
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        CustomUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_categories_skill'
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        CustomUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='updated_categories_skill'
    )

    def __str__(self):
        return self.name

