import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.db.models import JSONField




# class CustomUserManager(BaseUserManager):
#     def create_user(self, phone_number, password=None, **extra_fields):
#         if not phone_number:
#             raise ValueError("Phone number is required")
#         user = self.model(phone_number=phone_number, **extra_fields)
#         user.set_password(password)
#         user.save(using=self._db)
#         return user
    
#     def create_superuser(self, phone_number, password=None, **extra_fields):
#         extra_fields.setdefault("is_superuser", True)
#         extra_fields.setdefault("is_staff", True)
#         return self.create_user(phone_number, password, **extra_fields)


class CustomUserManager(BaseUserManager):
    def create_user(self, email=None, phone_number=None, password=None, **extra_fields):
        # Require either email or phone_number
        if not email and not phone_number:
            raise ValueError("Either email or phone number is required")
        
        if email:
            email = self.normalize_email(email)
        
        user = self.model(email=email, phone_number=phone_number, **extra_fields)
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone_number=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        
        if password is None:
            raise ValueError("Superuser must have a password")
        
        # Superuser needs phone_number
        if not phone_number:
            raise ValueError("Superuser must have a phone number")
        
        return self.create_user(email=email, phone_number=phone_number, password=password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    USER_TYPES = [
        ('worker', 'Worker'),
        ('employer', 'Employer'),
        ('admin', 'Admin'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    email = models.EmailField(max_length=255, unique=True, null=True, blank=True)
    password = models.CharField(max_length=255)  # Handled by AbstractBaseUser
    user_type = models.CharField(max_length=10, choices=USER_TYPES)
    full_name = models.CharField(max_length=255)
    profile_photo_url = models.URLField(max_length=500, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    is_oauth_user = models.BooleanField(default=False, null=True, blank=True)
    
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    is_staff = models.BooleanField(default=False)  # Required by Django admin

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.full_name} ({self.email})"
    

class OTPVerification(models.Model):
        OTP_TYPES = [
            ('registration', 'Registration'),
            ('login', 'Login'),
            ('password_reset', 'Password Reset'),
            ('phone_verification', 'Phone Verification'),
        ]

        id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
        user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="otp_verifications")
        phone_number = models.CharField(max_length=20, null=True, blank=True)
        email = models.EmailField(max_length=255, null=True, blank=True)
        otp_code = models.CharField(max_length=6)
        otp_type = models.CharField(max_length=20, choices=OTP_TYPES)
        expires_at = models.DateTimeField()
        verified_at = models.DateTimeField(null=True, blank=True)
        attempts = models.IntegerField(default=0)
        created_at = models.DateTimeField(default=timezone.now)

        def __str__(self):
            return f"OTP for {self.user.email} ({self.otp_type})"