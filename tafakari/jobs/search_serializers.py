from rest_framework import serializers
from .models import Job
from .serializers import JobSerializer


class JobSearchSerializer(JobSerializer):
    """
    Extended job serializer for search results with additional computed fields.
    Inherits conditional employer filtering from JobSerializer.
    """
    skill_names = serializers.SerializerMethodField()
    
    class Meta(JobSerializer.Meta):
        fields = JobSerializer.Meta.fields + ['skill_names']
    
    def get_skill_names(self, obj):
        """Return list of skill names for this job"""
        return [job_skill.skill.name for job_skill in obj.job_skills.all()]


class JobSearchQuerySerializer(serializers.Serializer):
    """
    Serializer to validate and process search query parameters
    """
    # Full-text search
    q = serializers.CharField(required=False, allow_blank=True, help_text="Search query for title and description")
    
    # Skill filtering
    skills = serializers.CharField(required=False, allow_blank=True, help_text="Comma-separated skill names or IDs")
    
    # Category filtering
    category = serializers.UUIDField(required=False, allow_null=True, help_text="Job category ID")
    
    # Location filtering
    location = serializers.CharField(required=False, allow_blank=True, help_text="Location text (partial match)")
    
    # Job type filtering
    job_type = serializers.ChoiceField(
        choices=Job.JobType.choices,
        required=False,
        allow_blank=True,
        help_text="Job type (part_time, full_time, temporary, contract)"
    )
    
    # Urgency level filtering
    urgency_level = serializers.ChoiceField(
        choices=Job.UrgencyLevel.choices,
        required=False,
        allow_blank=True,
        help_text="Urgency level (low, medium, high, urgent)"
    )
    
    # Payment type filtering
    payment_type = serializers.ChoiceField(
        choices=Job.PaymentType.choices,
        required=False,
        allow_blank=True,
        help_text="Payment type (hourly, daily, weekly, monthly, fixed)"
    )
    
    # Budget filtering
    budget_min = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text="Minimum budget"
    )
    budget_max = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text="Maximum budget"
    )
    
    # Sorting
    sort_by = serializers.ChoiceField(
        choices=[
            ('created_at', 'Created Date'),
            ('budget_min', 'Minimum Budget'),
            ('budget_max', 'Maximum Budget'),
            ('urgency_level', 'Urgency Level'),
            ('applications_count', 'Applications Count'),
            ('views_count', 'Views Count'),
        ],
        required=False,
        default='created_at',
        help_text="Field to sort by"
    )
    order = serializers.ChoiceField(
        choices=[('asc', 'Ascending'), ('desc', 'Descending')],
        required=False,
        default='desc',
        help_text="Sort order"
    )
    
    def validate_skills(self, value):
        """Validate and parse skills parameter"""
        if value:
            # Split by comma and strip whitespace
            skills_list = [skill.strip() for skill in value.split(',') if skill.strip()]
            return skills_list
        return []
    
    def validate(self, data):
        """Cross-field validation"""
        # Validate budget range
        budget_min = data.get('budget_min')
        budget_max = data.get('budget_max')
        
        if budget_min is not None and budget_max is not None:
            if budget_min > budget_max:
                raise serializers.ValidationError({
                    'budget_min': 'Minimum budget cannot be greater than maximum budget'
                })
        
        return data
