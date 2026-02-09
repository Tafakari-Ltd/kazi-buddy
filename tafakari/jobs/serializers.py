from rest_framework import serializers
from .models import Job,JobCategory,JobSkill
from skills.models import Skill
from employers.serializers import EmployerProfileSerializer

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
    employer = EmployerProfileSerializer(read_only=True)
    employer_name = serializers.CharField(source='employer.company_name', read_only=True)

    class Meta:
        model = Job

        fields = [
            'id', 'employer', 'employer_name', 'category', 'title', 'description', 'location',
            'location_text', 'job_type', 'urgency_level', 'budget_min',
            'budget_max', 'payment_type', 'start_date', 'end_date',
            'estimated_hours', 'max_applicants', 'status', 'visibility',
            'admin_approved', 'views_count', 'applications_count',
            'created_at', 'updated_at', 'expires_at', 'filled_at',
            'job_skills'
        ]
    
    def to_representation(self, instance):
        """
        Conditionally include employer details based on authentication status.
        Unauthenticated users only see employer_name, not the full employer object.
        """
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # Remove employer details if user is not authenticated
        if not request or not request.user.is_authenticated:
            data.pop('employer', None)
        
        return data


    def create(self, validated_data):
        skills_data = validated_data.pop('skills', [])
        # Set employer from request user
        validated_data['employer'] = self.context['request'].user.employerprofile
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

class FeaturedJobSerializer(serializers.ModelSerializer):
    """Serializer for featured jobs"""
    employer_name = serializers.CharField(source='employer.company_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Job
        fields = [
            'id', 'title','description', 'employer_name', 'category_name', 'location_text',
            'job_type', 'urgency_level', 'budget_min', 'budget_max', 
            'payment_type', 'created_at'
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
