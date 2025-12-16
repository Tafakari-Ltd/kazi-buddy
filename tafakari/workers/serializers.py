from rest_framework import serializers
from .models import WorkerProfile
from accounts.serializers import UserSerializer

class WorkerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = WorkerProfile
        fields = [
            'id', 'user', 'location', 'location_text', 'is_available',
            'years_experience', 'hourly_rate', 'availability_schedule',
            'bio', 'created_at', 'updated_at', 'profile_completion_percentage',
            'verification_status', 'admin_notes'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'updated_at',
            'profile_completion_percentage', 'verification_status', 'admin_notes'
        ]
