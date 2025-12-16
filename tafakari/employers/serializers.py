from rest_framework import serializers
from .models import EmployerProfile
from accounts.serializers import UserSerializer

class EmployerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = EmployerProfile
        fields = '__all__'
        read_only_fields = ['id', 'user', 'verification_status', 'admin_notes', 'created_at', 'updated_at']
