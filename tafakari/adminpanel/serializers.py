from rest_framework import serializers
from accounts.models import CustomUser


class ApproveUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'phone_number', 'is_verified', 'email_verified', 'phone_verified']

class UserStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'full_name', 'phone_number', 'email', 'is_active', 'is_verified']