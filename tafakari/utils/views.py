from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.utils.timezone import now
from django.conf import settings
from accounts.models import OTPVerification
from django.utils import timezone
import random
import supabase
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
    

def get_supabase_client():
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    return supabase.create_client(url, key) if url and key else None

def upload_file_to_supabase(file, filename, file_type, bucket_name='tafakari-uploads'):
    supabase_client = get_supabase_client()
    if not supabase_client:
        raise ValueError("Supabase client is not configured properly.")

    subfolder = file_type.lower()
    if subfolder not in ['documents', 'audio', 'video', 'images']:
        raise ValueError("Invalid file type. Must be one of: 'documents', 'audio', 'video', 'images'.")

    full_path = f"{subfolder}/{filename}"  # ✅ Don't include bucket name in path

    try:
        response = supabase_client.storage.from_(bucket_name).upload(
            full_path, file, file_options={"upsert": False}
        )
        return response
    except Exception as e:
        if "The resource already exists" in str(e):
            # ✅ File already exists — return existing key
            return full_path
        raise Exception(f"An error occurred during file upload: {str(e)}")

# def get_file_path_using_public_url(public_url, bucket_name='tafakari-uploads'):
#     supabase_client = get_supabase_client()
#     if not supabase_client:
#         raise ValueError("Supabase client is not configured properly.")

#     # Extract the file path from the public URL
#     if not public_url.startswith(f"https://{bucket_name}.supabase.co/storage/v1/object/public/"):
#         raise ValueError("Invalid public URL format.")

#     file_path = public_url.replace(f"https://{bucket_name}.supabase.co/storage/v1/object/public/tafakari-uploads/", "")
#     return file_path  # Return the file path in Supabase storage


def get_file_url_from_supabase(file_path, file_type, bucket_name='tafakari-uploads'):
    supabase_client = get_supabase_client()
    if not supabase_client:
        raise ValueError("Supabase client is not configured properly.")

    # Validate file_type
    subfolder = file_type.lower()
    if subfolder not in ['documents', 'audio', 'video', 'images']:
        raise ValueError("Invalid file type. Must be one of: 'documents', 'audio', 'video', 'images'.")

    # Correct path: should not include bucket name
    full_path = f"{subfolder}/{file_path}"

    response = supabase_client.storage.from_(bucket_name).get_public_url(full_path)

    # if not response or "publicURL" not in response:
    #     raise Exception("Failed to generate public URL")

    return response

def delete_file_from_supabase(file_name, file_type, bucket_name='tafakari-uploads'):
    supabase_client = get_supabase_client()
    if not supabase_client:
        raise ValueError("Supabase client is not configured properly.")

    # Determine the subfolder based on file_type
    subfolder = file_type.lower()
    if subfolder not in ['documents', 'audio', 'video', 'images']:
        raise ValueError("Invalid file type. Must be one of: 'documents', 'audio', 'video', 'images'.")

    full_path = f"{bucket_name}/{subfolder}/{file_name}"
    try:
        response = supabase_client.storage.from_(bucket_name).remove([full_path])
    except Exception as e:
        raise Exception(f"Failed to delete file: {str(e)}")

    return True  # Return True if deletion was successful

def get_file_metadata_from_supabase(file_path, file_type, bucket_name='tafakari-uploads'):
    supabase_client = get_supabase_client()
    if not supabase_client:
        raise ValueError("Supabase client is not configured properly.")

    # Determine the subfolder based on file_type
    subfolder = file_type.lower()
    if subfolder not in ['documents', 'audio', 'video', 'images']:
        raise ValueError("Invalid file type. Must be one of: 'documents', 'audio', 'video', 'images'.")

    full_path = f"{bucket_name}/{subfolder}/{file_path}"
    response = supabase_client.storage.from_(bucket_name).get_metadata(full_path)
    
    if response.error:
        raise Exception(f"Failed to get file metadata: {response.error.message}")

    return response.data  # Return the metadata of the file