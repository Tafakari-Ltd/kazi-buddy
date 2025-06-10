from rest_framework import serializers
from .models import Skill, SkillCategory
from accounts.serializers import UserSerializer



class SkillCategorySerializer(serializers.ModelSerializer):
    # Add created_by field
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = SkillCategory
        fields = ['id', 'name', 'description', 'icon_url', 'is_active', 'created_at', 'created_by']
        read_only_fields = ['id', 'created_at', 'created_by']  # Mark as read-only


class SkillSerializer(serializers.ModelSerializer):
    category = SkillCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=SkillCategory.objects.filter(is_active=True),
        source='category',
        write_only=True,
        required=False
    )
    # Add created_by field
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Skill
        fields = ['id', 'name', 'description', 'category', 'category_id', 
                 'is_active', 'created_at', 'created_by']
        read_only_fields = ['id', 'created_at', 'created_by']  # Mark as read-only