from rest_framework import serializers
from .models import Job,JobCategory,JobSkill
from skills.models import Skill

class JobCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobCategory
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']

    def create(self, validated_data):
        return JobCategory.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        return instance

class JobSkillSerializer(serializers.ModelSerializer):
    # skill = serializers.SlugRelatedField(slug_field='name', queryset=Skill.objects.all())

    class Meta:
        model = JobSkill
        fields = ['id', 'skill','job', 'is_required', 'experience_level']
        read_only_fields = ['id', 'job']
        extra_kwargs = {
            'is_required': {'required': False},
            'experience_level': {'required': False},
            'skill': {'required': False},
        }
class JobSerializer(serializers.ModelSerializer):
    category = JobCategorySerializer(read_only=True)
    job_skills = JobSkillSerializer(many=True, read_only=True)

    class Meta:
        model = Job

        fields = [
            'id', 'employer', 'category', 'title', 'description', 'location',
            'location_text', 'job_type', 'urgency_level', 'budget_min',
            'budget_max', 'payment_type', 'start_date', 'end_date',
            'estimated_hours', 'max_applicants', 'status', 'visibility',
            'admin_approved', 'views_count', 'applications_count',
            'created_at', 'updated_at', 'expires_at', 'filled_at',
            'job_skills'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'employer': {'required': False},
            'category': {'required': False},
            'location': {'required': False},
            'location_text': {'required': False},
            'budget_min': {'required': False},
            'budget_max': {'required': False},
            'start_date': {'required': False},
            'end_date': {'required': False},
            'estimated_hours': {'required': False},
            'max_applicants': {'required': False},
            'status': {'required': False},
            'visibility': {'required': False},
            'description': {'required': False},
            'job_type': {'required': False},
            'payment_type': {'required': False},
        }