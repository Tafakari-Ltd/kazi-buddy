from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser
from .serializers import RegisterUserSerializer, LoginSerializer,GoogleOAuthUserSerializer
from utils.views import get_tokens_for_user, send_otp_to_email,generate_otp,validate_otp,get_userType_fromToken
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
import requests
from django.urls import reverse
from django.shortcuts import redirect
from django.views import View
from django.shortcuts import render
from workers.models import WorkerProfile
from employers.models import EmployerProfile
from django.db import transaction
import jwt
import json
import requests
from utils.views import upload_file_to_supabase,get_file_url_from_supabase
from utils.custom_error import error_response
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

User = CustomUser


class RegisterView(APIView):
    def post(self, request):
        # Extract the file from the request
        profile_pic = request.FILES.get('profile_photo')

        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            # Atomic: user creation must fully succeed or roll back
            with transaction.atomic():
                user = serializer.save()

            # External I/O: file upload to Supabase — kept outside transaction
            if profile_pic:
                try:
                    file_name = f"profile_pics/{user.id}_{profile_pic.name}"
                    # Save the uploaded file temporarily to the filesystem
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                        for chunk in profile_pic.chunks():
                            temp_file.write(chunk)
                        temp_file_path = temp_file.name
                    
                    # Upload the file using its temporary path
                    profile_photo_url = upload_file_to_supabase(temp_file_path, file_name, 'images')

                    
                    # Clean up the temporary file
                    import os
                    os.remove(temp_file_path)
                    if profile_photo_url:
                        user.profile_photo_url = profile_photo_url
                        user.save()
                except Exception as e:
                    print(f"Failed to upload profile picture: {str(e)}")

            # External I/O: OTP generation + email — kept outside transaction
            try:
                otp_code = generate_otp(user, 'registration')
                send_otp_to_email(user, otp_code, 'registration')
                print(f"OTP sent to {user.email}: {otp_code}")
            except Exception as e:
                # Handle email failure (log error, don't block registration)
                print(f"OTP email failed: {str(e)}")

            return Response({
                "message": "User registered. Check email for verification OTP",
                "user_id": str(user.id),
                "user_data": {
                    "phone_number": user.phone_number,
                    "email": user.email,
                    "user_type": user.user_type,
                    "full_name": user.full_name,
                    "profile_photo_url": user.profile_photo_url,
                },
            }, status=status.HTTP_201_CREATED)
        return error_response(
            message="error during register",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            if not user.email_verified :
                return Response({"error": "Email not verified. Please verify your email before logging in."}, status=status.HTTP_403_FORBIDDEN)
            else:
                if not user.is_verified:
                    return Response({"error": "You are not approved by admin yet. Please wait for approval."}, status=status.HTTP_403_FORBIDDEN)
            
            tokens = get_tokens_for_user(user)
            user_type = get_userType_fromToken(tokens['access'])
            otp_code = generate_otp(user, 'login')
            send_otp_to_email(user, otp_code, 'login')
            return Response({
                "message": "Login successful",
                "user_id": str(user.id),
                "user_type": user_type,
                "tokens": tokens
            })
        # return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
        return error_response(
            message="error during login",
            errors=serializer.errors,
            status_code=status.HTTP_401_UNAUTHORIZED
        )

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = settings.GOOGLE_OAUTH_CALLBACK_URL



class GoogleLoginCallback(APIView):
    def get(self, request):
        try:
           
            # Handle Google OAuth errors
           
            error = request.GET.get("error")
            if error:
                message = request.GET.get("error_description", "Google authentication failed")
                return redirect(
                    f"{settings.FRONTEND_URL}/auth/login"
                    f"?status=error&message={message}"
                )

            # Get authorization code
            
            code = request.GET.get("code")
            if not code:
                return redirect(
                    f"{settings.FRONTEND_URL}/auth/login"
                    f"?status=error&message=Authorization code not provided"
                )

            
            # Get and validate user_type from state parameter
            
            state_param = request.GET.get("state")
            requested_user_type = "worker"  # default
            
            if state_param:
                try:
                    state_data = json.loads(state_param)
                    requested_user_type = state_data.get("user_type", "worker")
                except json.JSONDecodeError:
                    # If state parsing fails, default to worker
                    pass
            
            ALLOWED_USER_TYPES = {"worker", "employer"}

            user_type = (
                requested_user_type
                if requested_user_type in ALLOWED_USER_TYPES
                else "worker"
            )

            
            # Exchange code for tokens
            
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                "code": code,
                "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
                "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_OAUTH_CALLBACK_URL,
                "grant_type": "authorization_code",
            }

            try:
                response = requests.post(token_url, data=data)
                response.raise_for_status()
                token_data = response.json()
            except requests.exceptions.RequestException:
                return redirect(
                    f"{settings.FRONTEND_URL}/auth/login"
                    f"?status=error&message=Failed to exchange authorization code"
                )

            if "error" in token_data:
                return redirect(
                    f"{settings.FRONTEND_URL}/auth/login"
                    f"?status=error&message=Token exchange failed"
                )

            if "id_token" not in token_data:
                return redirect(
                    f"{settings.FRONTEND_URL}/auth/login"
                    f"?status=error&message=No ID token received from Google"
                )

           
            # Verify ID token
            
            try:
                decoded_token = id_token.verify_oauth2_token(
                    token_data["id_token"],
                    google_requests.Request(),
                    settings.GOOGLE_OAUTH_CLIENT_ID
                )
            except Exception:
                return redirect(
                    f"{settings.FRONTEND_URL}/auth/login"
                    f"?status=error&message=Invalid Google token"
                )

            # Extract user info
            
            email = decoded_token.get("email")
            name = decoded_token.get("name", "")
            picture = decoded_token.get("picture", "")

            if not email:
                return redirect(
                    f"{settings.FRONTEND_URL}/auth/login"
                    f"?status=error&message=Email not provided by Google"
                )

           
            # Existing user flow
            
            try:
                user = CustomUser.objects.get(email=email)

                if not user.is_verified:
                    message = (
                        "Your account is pending admin approval. "
                        "Please wait for approval before logging in."
                    )
                    return redirect(
                        f"{settings.FRONTEND_URL}/auth/login"
                        f"?status=pending_approval&message={message}"
                    )

                tokens = get_tokens_for_user(user)
                user_type_from_token = get_userType_fromToken(tokens["access"])

                return redirect(
                    f"{settings.FRONTEND_URL}/auth/google/success"
                    f"?access_token={tokens['access']}"
                    f"&refresh_token={tokens['refresh']}"
                    f"&user_id={user.id}"
                    f"&user_type={user_type_from_token}"
                )

            
            # New user flow - Registration
            
            except CustomUser.DoesNotExist:
                try:
                    # Double-check email uniqueness before creating account
                    # This prevents race conditions and ensures data integrity
                    if CustomUser.objects.filter(email=email).exists():
                        message = (
                            "An account with this email already exists. "
                            "Please try logging in instead."
                        )
                        return redirect(
                            f"{settings.FRONTEND_URL}/auth/login"
                            f"?status=error&message={message}"
                        )
                    
                    user_data = {
                        "email": email,
                        "full_name": name,
                        "user_type": user_type,
                        "profile_photo_url": picture,
                    }

                    serializer = GoogleOAuthUserSerializer(data=user_data)

                    if serializer.is_valid():
                        serializer.save()
                        message = (
                            "Account created successfully! "
                            "Your account is pending admin approval."
                        )
                        return redirect(
                            f"{settings.FRONTEND_URL}/auth/login"
                            f"?status=pending_approval&message={message}"
                        )

                    # If serializer validation fails, return error
                    error_message = "Failed to create user account"
                    if serializer.errors:
                        # Extract first error message for user-friendly display
                        first_error = next(iter(serializer.errors.values()))[0]
                        error_message = str(first_error)
                    
                    return redirect(
                        f"{settings.FRONTEND_URL}/auth/login"
                        f"?status=error&message={error_message}"
                    )

                except Exception as e:
                    # Log the exception for debugging
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Google OAuth registration error: {str(e)}")
                    
                    return redirect(
                        f"{settings.FRONTEND_URL}/auth/login"
                        f"?status=error&message=Failed to create user"
                    )

    
        # Catch-all safeguard
        
        except Exception:
            return redirect(
                f"{settings.FRONTEND_URL}/auth/login"
                f"?status=error&message=Unexpected authentication error"
            )


# class GoogleLoginCallback(APIView):
#     def get(self, request):
#         try:
#             # Check for errors from Google
#             error = request.GET.get('error')
#             if error:
#                 return Response({
#                     "error": f"Google OAuth error: {error}",
#                     "description": request.GET.get('error_description', 'No description')
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             # Get authorization code from Google
#             code = request.GET.get('code')
            
#             if not code:
#                 return Response({
#                     "error": "Authorization code not provided"
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             requested_user_type = request.GET.get("user_type", "worker")

#             ALLOWED_USER_TYPES = {"worker","employer"}
#             user_type = (
#                 requested_user_type
#                 if requested_user_type in ALLOWED_USER_TYPES
#                 else "worker"
#             )
            
#             # Exchange authorization code for tokens
#             token_url = 'https://oauth2.googleapis.com/token'
#             data = {
#                 'code': code,
#                 'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
#                 'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
#                 'redirect_uri': settings.GOOGLE_OAUTH_CALLBACK_URL,
#                 'grant_type': 'authorization_code',
#             }
            
#             try:
#                 response = requests.post(token_url, data=data)
#                 response.raise_for_status()
#                 token_data = response.json()
#             except requests.exceptions.RequestException as e:
#                 return Response({
#                     "error": "Failed to exchange code for tokens",
#                     "details": str(e)
#                 }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
#             # Check for errors in token response
#             if 'error' in token_data:
#                 return Response({
#                     "error": "Token exchange failed",
#                     "details": token_data
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             if 'id_token' not in token_data:
#                 return Response({
#                     "error": "No id_token received",
#                     "received_fields": list(token_data.keys())
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             # Verify and decode the ID token
#             try:
#                 decoded_token = id_token.verify_oauth2_token(
#                     token_data['id_token'],
#                     google_requests.Request(),
#                     settings.GOOGLE_OAUTH_CLIENT_ID
#                 )
#             except Exception as e:
#                 return Response({
#                     "error": "Invalid token",
#                     "details": str(e)
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             # Extract user information
#             email = decoded_token.get('email')
#             name = decoded_token.get('name', '')
#             picture = decoded_token.get('picture', '')
            
#             if not email:
#                 return Response({
#                     "error": "Email not provided by Google"
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             # Check if user already exists
#             try:
#                 user = CustomUser.objects.get(email=email)
                
#                 # Check if user is verified by admin
#                 if not user.is_verified:
#                     return Response({
#                         "error": "Account pending approval",
#                         "message": "Your account has been created but is pending admin approval. Please wait for approval before logging in.",
#                         "user_id": str(user.id),
#                         "email": user.email
#                     }, status=status.HTTP_403_FORBIDDEN)
                
#                 # User exists and is approved - log them in
#                 tokens = get_tokens_for_user(user)
#                 user_type = get_userType_fromToken(tokens['access'])
                
#                 return Response({
#                     "message": "Welcome back! Google login successful",
#                     "user_id": str(user.id),
#                     "tokens": tokens,
#                     "user_created": False,
#                     "user_info": {
#                         "email": email,
#                         "name": user.full_name,
#                         "profile_photo_url": user.profile_photo_url or picture,
#                         "user_type": user_type,
#                     }
#                 }, status=status.HTTP_200_OK)
                    
#             except CustomUser.DoesNotExist:
#                 # User doesn't exist - create new user with default user_type
#                 try:
#                     # Prepare user data - default to 'worker' user_type
#                     # Admin will assign the correct role after approval
#                     user_data = {
#                         'email': email,
#                         'full_name': name,
#                         'user_type': user_type,
#                         'profile_photo_url': picture,
#                     }
                    
#                     # Create user with GoogleOAuthUserSerializer
#                     serializer = GoogleOAuthUserSerializer(data=user_data)
                    
#                     if serializer.is_valid():
#                         user = serializer.save()
                        
#                         # Note: is_verified is False by default (set in serializer)
#                         # User must wait for admin approval before logging in
                        
#                         return Response({
#                             "message": "Account created successfully! Pending admin approval.",
#                             "user_id": str(user.id),
#                             "user_created": True,
#                             "pending_approval": True,
#                             "user_info": {
#                                 "email": email,
#                                 "name": name,
#                                 "profile_photo_url": picture,
#                             },
#                             "note": "Your account has been created but requires admin approval before you can log in. You will be notified once approved."
#                         }, status=status.HTTP_201_CREATED)
#                     else:
#                         return Response({
#                             "error": "Failed to create user",
#                             "details": serializer.errors
#                         }, status=status.HTTP_400_BAD_REQUEST)
                    
#                 except Exception as e:
#                     return Response({
#                         "error": "Failed to create user",
#                         "details": str(e)
#                     }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#         except Exception as e:
#             # Catch any unexpected exceptions
#             import traceback
#             return Response({
#                 "error": "Unexpected error in Google callback",
#                 "details": str(e),
#                 "traceback": traceback.format_exc()
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# #for testing purposes


class LoginPage(View):
    def get(self, request, *args, **kwargs):
        return render(
            request,
            "pages/login.html",
            {
                "google_callback_uri": settings.GOOGLE_OAUTH_CALLBACK_URL,
                "google_client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            },
        )
  

class UserProfileView(APIView):
    def get(self, request):
        try:
            if not request.user.is_authenticated:
                return Response(
                    {
                        "status": "error",
                        "message": "Authentication required",
                        "stack": {},
                        "error": {
                            "statusCode": status.HTTP_401_UNAUTHORIZED,
                            "status": "error"
                        }
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            user = request.user
            return Response({
                "user_id": str(user.id),
                "email": user.email,
                "phone_number": user.phone_number,
                "user_type": user.user_type,
                "full_name": user.full_name,
                "profile_photo_url": user.profile_photo_url,
                "email_verified": user.email_verified,
                "phone_verified": user.phone_verified,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return error_response(
                message="Error retrieving user profile",
                errors={"error": str(e)},
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        

class UpdateUserProfileView(APIView):
        def put(self, request):
            if not request.user.is_authenticated:
                # return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
                return Response(
                    {
                        "status": "error",
                        "message": "Error updating user profile",
                        "stack": {"error": "Authentication required"},
                        "error": {
                            "statusCode": status.HTTP_401_UNAUTHORIZED,
                            "status": "error"
                        }
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            user = request.user
            data = request.data
            
            # Update user fields
            user.full_name = data.get("full_name", user.full_name)
            user.phone_number = data.get("phone_number", user.phone_number)
            user.profile_photo_url = data.get("profile_photo_url", user.profile_photo_url)
            
            print(f"user photo url: {user.profile_photo_url}")
            try:
                user.save()
                return Response({
                    "message": "Profile updated successfully",
                    "user_id": str(user.id),
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "user_type": user.user_type,
                    "full_name": user.full_name,
                    "profile_photo_url": user.profile_photo_url,
                    "email_verified": user.email_verified,
                    "phone_verified": user.phone_verified,
                }, status=status.HTTP_200_OK)
            except Exception as e:
                # return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                return error_response(
                    message="Error updating user profile",
                    errors={"error": str(e)},
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    
class LogoutView(APIView):
    def post(self, request):
        if not request.user.is_authenticated:
            # return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            return error_response(
                message="Error during logout",
                errors={"error": "Authentication required"},
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        # Invalidate the user's tokens
        try:
            RefreshToken.for_user(request.user)
            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        except Exception as e:
            # return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return error_response(
                message="Error during logout",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class DeleteAccountView(APIView):
    def delete(self, request):
        if not request.user.is_authenticated:
            return error_response(
                message="Error deleting account",
                errors={"error": "Authentication required"},
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        user = request.user
        try:
            user.delete()
            return Response({"message": "Account deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return error_response(
                message="Error deleting account",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
                

class VerifyEmailView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        otp_code = request.data.get('otp_code')
        otp_type = request.data.get('otp_type')
        
        try:         
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist as e:
            return error_response(
                message="User not found",
                errors={"error": str(e)},
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Atomic: OTP validation + email_verified flag must succeed or fail together
            with transaction.atomic():
                if validate_otp(user, otp_code, otp_type):
                    user.email_verified = True
                    user.save()
                else:
                    return error_response(
                        message="Invalid or expired OTP",
                        errors={"error": "Invalid or expired OTP"},
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
            return Response({"message": "Email verified successfully"})
            
        except Exception as e:
            return error_response(
                message="Error verifying email",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PasswordResetView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return error_response(
                message="User with this email does not exist",
                errors={"error": "User with this email does not exist"},
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        otp_code = generate_otp(user, 'password_reset')
        send_otp_to_email(user, otp_code, 'password_reset')
        
        return Response({
            "message": "Password reset OTP sent to your email",
            "user_id": str(user.id)
        }, status=status.HTTP_200_OK)

