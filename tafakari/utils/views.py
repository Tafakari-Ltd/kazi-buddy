from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken,AccessToken
# from django.core.mail import send_mail  # Commented out - using smtplib instead
from django.utils.timezone import now
from django.conf import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from accounts.models import OTPVerification
from django.utils import timezone
from django.template.loader import render_to_string
from threading import Thread
import random
import supabase
import logging



logger = logging.getLogger(__name__)

# Create your views here.
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    # Add custom claims to the token
    refresh['user_type'] = user.user_type if hasattr(user, 'user_type') else None
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def get_userType_fromToken(token):
    try:
        # Try decoding as Access token
        try:
            access = AccessToken(token)
            return access.get('user_type', None)
            
        except Exception:
            # If not access, fallback to refresh
            refresh = RefreshToken(token)
            return refresh.get('user_type', None)
    except Exception as e:
        logger.error(f"Error decoding token: {str(e)}")
        return None


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

# def send_otp_to_email(user, otp_code, otp_type):
#     try:
#         if not user.email:
#             raise ValueError("User does not have an email address.")

#         subject = f"{otp_type.capitalize()} OTP Verification"
#         recipient_list = [user.email]
#         context = {
#             'full_name': getattr(user, 'full_name', user.email),
#             'otp_code': otp_code,
#             'otp_type': otp_type.capitalize(),
#         }

#         try:
#             html_message = render_to_string(f'email_templates/{otp_type}_otp_email.html', context)
#         except Exception as template_error:
#             logger.error(f"Error rendering email template: {str(template_error)}")
#             raise Exception("Failed to render email template.")

#         try:
#             send_mail(
#                 subject,
#                 '',  # plain text message (optional, leave empty if only HTML)
#                 settings.DEFAULT_FROM_EMAIL,
#                 recipient_list,
#                 fail_silently=False,
#                 html_message=html_message,
#             )
#         except Exception as mail_error:
#             logger.error(f"Error sending OTP email: {str(mail_error)}")
#             raise Exception("Failed to send OTP email.")

#     except Exception as e:
#         logger.error(f"send_otp_to_email error: {str(e)}")
#         raise


# Django send_mail implementation
# def send_email_async(subject, html_message, recipient_list):
#     """Send email in a separate thread to avoid blocking"""
#     def _send():
#         try:
#             send_mail(
#                 subject,
#                 '',  # plain text message
#                 settings.DEFAULT_FROM_EMAIL,
#                 recipient_list,
#                 fail_silently=False,
#                 html_message=html_message,
#                 # timeout=20,  # Add timeout to prevent hanging
#             )
#             logger.info(f"Email sent successfully to {recipient_list}")
#         except Exception as e:
#             logger.error(f"Failed to send email: {str(e)}")
#     
#     thread = Thread(target=_send)
#     thread.daemon = True  # Thread will not block app shutdown
#     thread.start()


def send_email_async(subject, html_message, recipient_list):
    """Send email in a separate thread using smtplib to avoid blocking"""
    def _send():
        try:
            # Get email configuration from Django settings
            email_host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
            email_port = getattr(settings, 'EMAIL_PORT', 587)
            email_host_user = getattr(settings, 'EMAIL_HOST_USER', settings.DEFAULT_FROM_EMAIL)
            email_host_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
            use_tls = getattr(settings, 'EMAIL_USE_TLS', True)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.DEFAULT_FROM_EMAIL
            msg['To'] = ', '.join(recipient_list)
            
            # Attach HTML content
            html_part = MIMEText(html_message, 'html')
            msg.attach(html_part)
            
            # Send email using SMTP
            if use_tls:
                server = smtplib.SMTP(email_host, email_port, timeout=20)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(email_host, email_port, timeout=20)
            
            if email_host_password:
                server.login(email_host_user, email_host_password)
            
            server.sendmail(settings.DEFAULT_FROM_EMAIL, recipient_list, msg.as_string())
            server.quit()
            
            logger.info(f"Email sent successfully to {recipient_list}")
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
    
    thread = Thread(target=_send)
    thread.daemon = True  # Thread will not block app shutdown
    thread.start()



def send_otp_to_email(user, otp_code, otp_type):
    """
    Send OTP email asynchronously to avoid blocking the request
    """
    try:
        # Validate user email
        if not user.email:
            logger.error(f"User {user.id} does not have an email address")
            raise ValueError("User does not have an email address.")
        
        # Prepare email content
        subject = f"{otp_type.capitalize()} OTP Verification"
        recipient_list = [user.email]
        context = {
            'full_name': getattr(user, 'full_name', user.email),
            'otp_code': otp_code,
            'otp_type': otp_type.capitalize(),
        }
        
        # Render email template
        try:
            html_message = render_to_string(
                f'email_templates/{otp_type}_otp_email.html', 
                context
            )
        except Exception as template_error:
            logger.error(f"Error rendering email template: {str(template_error)}")
            raise Exception("Failed to render email template.")
        
        # Send email asynchronously
        send_email_async(subject, html_message, recipient_list)
        
        logger.info(f"OTP email queued for {user.email}")
        
    except Exception as e:
        logger.error(f"send_otp_to_email error: {str(e)}")
        # Don't raise - let the user continue even if email fails
        # The OTP is still saved in the database
        pass

def validate_otp(user, otp_code, otp_type):
    # Atomic: OTP lookup + mark verified must be atomic with select_for_update
    # to prevent the same OTP from being validated concurrently by two requests
    from django.db import transaction
    try:
        with transaction.atomic():
            otp_record = OTPVerification.objects.select_for_update().get(
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
    """Get Supabase client with proper error handling"""
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    
    if not url or not key:
        logger.error("Supabase URL or KEY not configured")
        return None
    
    try:
        client = supabase.create_client(url, key)
        return client
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {str(e)}")
        return None

def upload_file_to_supabase(file_path, filename, file_type, bucket_name='tafakari'):
    """Upload file to Supabase with improved error handling"""
    supabase_client = get_supabase_client()
    if not supabase_client:
        raise ValueError("Supabase client is not configured properly.")
    
    # Validate file_type
    subfolder = file_type.lower()
    if subfolder not in ['documents', 'audio', 'video', 'images']:
        raise ValueError("Invalid file type. Must be one of: 'documents', 'audio', 'video', 'images'.")
    
    full_path = f"{subfolder}/{filename}"
    
    try:
        # Check if file exists first
        try:
            existing = supabase_client.storage.from_(bucket_name).list(subfolder, {
                "limit": 100,
                "search": filename
            })
            # If file exists, optionally skip or update
            if existing and any(item.get('name') == filename for item in existing):
                logger.info(f"File {filename} already exists, skipping upload")
                return supabase_client.storage.from_(bucket_name).get_public_url(full_path)
        except Exception as list_error:
            logger.warning(f"Could not check existing files: {str(list_error)}")
        
        # Upload the file
        with open(file_path, 'rb') as file_obj:
            file_content = file_obj.read()
            
            # Determine content type
            content_type = "text/plain"
            if file_type == 'images':
                content_type = "image/png"
            elif file_type == 'documents':
                if filename.endswith('.pdf'):
                    content_type = "application/pdf"
                elif filename.endswith('.txt'):
                    content_type = "text/plain"
            
            response = supabase_client.storage.from_(bucket_name).upload(
                path=full_path,
                file=file_content,
                file_options={
                    "content-type": content_type,
                    "upsert": False
                }
            )
            
            # Check if response indicates success
            if hasattr(response, 'error') and response.error:
                raise Exception(f"Upload failed: {response.error}")
            
        # Return public URL
        public_url = supabase_client.storage.from_(bucket_name).get_public_url(full_path)
        return public_url
        
    except Exception as e:
        if "already exists" in str(e).lower():
            # File exists, return its URL
            return supabase_client.storage.from_(bucket_name).get_public_url(full_path)
        else:
            logger.error(f"Upload error: {str(e)}")
            raise Exception(f"An error occurred during file upload: {str(e)}")

def get_file_url_from_supabase(file_path, file_type, bucket_name='tafakari'):
    """Get public URL for file from Supabase"""
    supabase_client = get_supabase_client()
    if not supabase_client:
        raise ValueError("Supabase client is not configured properly.")
    
    # Validate file_type
    subfolder = file_type.lower()
    if subfolder not in ['documents', 'audio', 'video', 'images']:
        raise ValueError("Invalid file type. Must be one of: 'documents', 'audio', 'video', 'images'.")
    
    full_path = f"{subfolder}/{file_path}"
    
    try:
        response = supabase_client.storage.from_(bucket_name).get_public_url(full_path)
        return response
    except Exception as e:
        logger.error(f"Error getting file URL: {str(e)}")
        raise Exception(f"Failed to get file URL: {str(e)}")

def delete_file_from_supabase(file_name, file_type, bucket_name='tafakari'):
    """Delete file from Supabase with better error handling"""
    supabase_client = get_supabase_client()
    if not supabase_client:
        raise ValueError("Supabase client is not configured properly.")
    
    # Validate file_type
    subfolder = file_type.lower()
    if subfolder not in ['documents', 'audio', 'video', 'images']:
        raise ValueError("Invalid file type. Must be one of: 'documents', 'audio', 'video', 'images'.")
    
    full_path = f"{subfolder}/{file_name}"
    
    try:
        # First check if file exists
        try:
            files = supabase_client.storage.from_(bucket_name).list(subfolder)
            file_exists = any(item.get('name') == file_name for item in files if files)
            
            if not file_exists:
                logger.warning(f"File {file_name} not found in {subfolder}")
                return True  # Consider non-existent file as successfully "deleted"
        except Exception as list_error:
            logger.warning(f"Could not list files to check existence: {str(list_error)}")
        
        # Attempt deletion
        response = supabase_client.storage.from_(bucket_name).remove([full_path])
        
        # Check response for errors
        if hasattr(response, 'error') and response.error:
            raise Exception(f"Delete API error: {response.error}")
        
        return True
        
    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        # Don't raise exception for "file not found" scenarios
        if "not found" in str(e).lower() or "does not exist" in str(e).lower():
            return True
        raise Exception(f"Failed to delete file: {str(e)}")

def get_file_metadata_from_supabase(file_path, file_type, bucket_name='tafakari'):
    """Get file metadata from Supabase"""
    supabase_client = get_supabase_client()
    if not supabase_client:
        raise ValueError("Supabase client is not configured properly.")
    
    subfolder = file_type.lower()
    if subfolder not in ['documents', 'audio', 'video', 'images']:
        raise ValueError("Invalid file type. Must be one of: 'documents', 'audio', 'video', 'images'.")
    
    full_path = f"{subfolder}/{file_path}"
    
    try:
        response = supabase_client.storage.from_(bucket_name).get_metadata(full_path)
        
        if hasattr(response, "error") and response.error:
            raise Exception(f"Failed to get file metadata: {response.error.message}")
        
        return getattr(response, "data", response)
    except Exception as e:
        logger.error(f"Error getting metadata: {str(e)}")
        raise Exception(f"Failed to get file metadata: {str(e)}")
