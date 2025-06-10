# serializers.py
from rest_framework import serializers
from django.db.models import Q
from .models import Job, JobCategory, JobSkill
from employers.models import EmployerProfile
from skills.models import Skill


class JobCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobCategory
        fields = ['id', 'name', 'description', 'icon_url']


class JobSkillSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    
    class Meta:
        model = JobSkill
        fields = ['id', 'skill', 'skill_name', 'is_required', 'experience_level']


class JobListSerializer(serializers.ModelSerializer):
    """Serializer for job list view with minimal fields"""
    employer_name = serializers.CharField(source='employer.company_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Job
        fields = [
            'id', 'title', 'employer_name', 'category_name', 'location_text',
            'job_type', 'urgency_level', 'budget_min', 'budget_max', 
            'payment_type', 'created_at', 'views_count', 'applications_count'
        ]


class JobDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed job view"""
    employer_name = serializers.CharField(source='employer.company_name', read_only=True)
    employer_id = serializers.UUIDField(source='employer.id', read_only=True)
    category = JobCategorySerializer(read_only=True)
    job_skills = JobSkillSerializer(many=True, read_only=True)
    
    class Meta:
        model = Job
        fields = [
            'id', 'employer_id', 'employer_name', 'category', 'title', 
            'description', 'location', 'location_text', 'job_type', 
            'urgency_level', 'budget_min', 'budget_max', 'payment_type',
            'start_date', 'end_date', 'estimated_hours', 'max_applicants',
            'status', 'visibility', 'views_count', 'applications_count',
            'job_skills', 'created_at', 'updated_at', 'expires_at'
        ]


class JobCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating jobs"""
    skills = serializers.ListField(
        child=serializers.DictField(), 
        write_only=True, 
        required=False,
        help_text="List of skills with format: [{'skill_id': 'uuid', 'is_required': true, 'experience_level': 'intermediate'}]"
    )
    
    class Meta:
        model = Job
        fields = [
            'category', 'title', 'description', 'location', 'location_text',
            'job_type', 'urgency_level', 'budget_min', 'budget_max',
            'payment_type', 'start_date', 'end_date', 'estimated_hours',
            'max_applicants', 'visibility', 'expires_at', 'skills'
        ]
    
    def create(self, validated_data):
        skills_data = validated_data.pop('skills', [])
        # Set employer from request user
        validated_data['employer'] = self.context['request'].user.employer_profile
        job = Job.objects.create(**validated_data)
        
        # Create job skills
        self._create_job_skills(job, skills_data)
        return job
    
    def update(self, instance, validated_data):
        skills_data = validated_data.pop('skills', None)
        
        # Update job fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update skills if provided
        if skills_data is not None:
            instance.job_skills.all().delete()
            self._create_job_skills(instance, skills_data)
        
        return instance
    
    def _create_job_skills(self, job, skills_data):
        for skill_data in skills_data:
            JobSkill.objects.create(
                job=job,
                skill_id=skill_data.get('skill_id'),
                is_required=skill_data.get('is_required', True),
                experience_level=skill_data.get('experience_level', 'intermediate')
            )
