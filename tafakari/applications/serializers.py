from .models import JobApplication, WorkerInvitation
from jobs.serializers import JobSerializer
from workers.serializers import WorkerProfileSerializer

from rest_framework import serializers

class JobApplicationSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    worker = WorkerProfileSerializer(read_only=True)
    class Meta:
        model = JobApplication
        fields = '__all__'
        read_only_fields = ('id', 'applied_at', 'reviewed_at', 'responded_at','status','worker')
        extra_kwargs = {
            'proposed_rate': {'required': True, 'min_value': 0},
            'availability_start': {'required': True},
            'cover_letter': {'required': False, 'allow_blank': True},
            'worker_notes': {'required': False, 'allow_blank': True},
            'employer_notes': {'required': False, 'allow_blank': True},
            'job': {'required': False, 'write_only': False},
        }
        def validate(self, data):
            if data['proposed_rate'] < 0:
                raise serializers.ValidationError("Proposed rate must be a non-negative value.")
            return data
        def create(self, validated_data):
            # Automatically set the worker from the request context
            validated_data['worker'] = self.context['request'].user.workerprofile
            return super().create(validated_data)