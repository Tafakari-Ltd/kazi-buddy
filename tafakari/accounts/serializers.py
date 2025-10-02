from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser
from dj_rest_auth.registration.serializers import RegisterSerializer


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    

    class Meta:
        model = CustomUser
        fields = ['phone_number', 'email', 'password', 'user_type', 'full_name','username']
        

    

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()  # Can be phone_number or email
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        identifier = data.get('identifier')
        password = data.get('password')

        try:
            user = CustomUser.objects.get(phone_number=identifier)
        except CustomUser.DoesNotExist:
            try:
                user = CustomUser.objects.get(email=identifier)
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError("Invalid phone number or email")

        if not user.check_password(password):
            raise serializers.ValidationError("Incorrect password")
        if not user.is_active:
            raise serializers.ValidationError("User account is inactive")

        return {"user": user}


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'full_name', 'email']
        read_only_fields = ['id', 'full_name', 'email']
    




class CustomRegisterSerializer(RegisterSerializer):
    username = None  # Explicitly remove the username field

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['email'] = self.validated_data.get('email', '')
        data['password1'] = self.validated_data.get('password', '')
        return data
