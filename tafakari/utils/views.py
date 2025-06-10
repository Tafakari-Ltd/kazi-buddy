from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.utils.timezone import now
from django.conf import settings
from accounts.models import OTPVerification
from django.utils import timezone
import random

# Create your views here.
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    # Add custom claims to the token
    refresh['user_type'] = user.user_type if hasattr(user, 'user_type') else None
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def generate_otp(user, otp_type, expiration_minutes=5):
    otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    expires_at = timezone.now() + timezone.timedelta(minutes=expiration_minutes)
    
    OTPVerification.objects.create(
        user=user,
        email=user.email,
        otp_code=otp_code,
        otp_type=otp_type,
        expires_at=expires_at
    )
    return otp_code

def send_otp_to_email(user, otp_code, otp_type):
    subject = f"{otp_type.capitalize()} OTP Verification"
    recipient_list = [user.email]

    if not user.email:
        raise ValueError("User does not have an email address.")

    context = {
        'full_name': user.full_name,
        'otp_code': otp_code,
        'otp_type': otp_type.capitalize(),
    }

    html_message = render(None, f'email_templates/{otp_type}_otp_email.html', context).content.decode()

    send_mail(
        subject,
        '',
        settings.EMAIL_HOST_USER,
        recipient_list,
        fail_silently=False,
        html_message=html_message,
    )





def validate_otp(user, otp_code, otp_type):
    try:
        otp_record = OTPVerification.objects.get(
            user=user,
            otp_code=otp_code,
            otp_type=otp_type,
            verified_at__isnull=True,
            expires_at__gt=timezone.now()
        )
        otp_record.verified_at = timezone.now()
        otp_record.save()
        return True
    except OTPVerification.DoesNotExist:
        return False