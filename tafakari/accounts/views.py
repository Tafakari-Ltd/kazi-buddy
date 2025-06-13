from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser
from .serializers import RegisterUserSerializer, LoginSerializer
from utils.views import get_tokens_for_user, send_otp_to_email,generate_otp,validate_otp
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from workers.models import WorkerProfile
from employers.models import EmployerProfile
from django.conf import settings
import requests
from django.urls import reverse
from django.views import View
from django.shortcuts import render
import jwt
import json
import requests
from django.db import transaction

User = CustomUser



from django.http import HttpResponse

def home(request):
    return HttpResponse("Hello, world! This is the home page.")


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            

            with transaction.atomic():
                user = serializer.save()
                if user.user_type == 'worker':
                    try:
                        WorkerProfile.objects.create(user=user)
                    except Exception as e:
                        # Handle any errors during profile creation
                        print(f"Error creating worker profile: {str(e)}")
                        return Response({"error": "Failed to create worker profile"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                elif user.user_type == 'employer':
                    try:
                        EmployerProfile.objects.create(user=user)
                    except Exception as e:
                        # Handle any errors during profile creation
                        print(f"Error creating employer profile: {str(e)}")
                        return Response({"error": "Failed to create employer profile"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                        
            # Generate and send verification OTP
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
                },
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = get_tokens_for_user(user)
            otp_code = generate_otp(user, 'login')
            send_otp_to_email(user, otp_code, 'login')
            return Response({
                "message": "Login successful",
                "user_id": str(user.id),
                "tokens": tokens
            })
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = settings.GOOGLE_OAUTH_CALLBACK_URL






class GoogleLoginCallback(APIView):
    def get(self, request):
        code = request.GET.get('code')
        if not code:
            return Response({"error": "Authorization code not provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Exchange the authorization code for tokens
        token_url = 'https://oauth2.googleapis.com/token'
        data = {
            'code': code,
            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
            'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
            'redirect_uri': settings.GOOGLE_OAUTH_CALLBACK_URL,
            'grant_type': 'authorization_code',
        }
        
        response = requests.post(token_url, data=data)
        token_data = response.json()
        
        if 'id_token' not in token_data:
            return Response({"error": "No id_token received"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Decode the JWT token to get user info
        try:
            decoded_token = jwt.decode(
                token_data['id_token'],
                options={"verify_signature": False}
            )
        except jwt.DecodeError:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
        
        email = decoded_token.get('email')
        name = decoded_token.get('name', '')
        picture = decoded_token.get('picture', '')
        
        if not email:
            return Response({"error": "Email not provided by Google"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check for existing user first
        try:
            user = CustomUser.objects.get(email=email)
            created = False
            
            # User already exists - log them in
            tokens = get_tokens_for_user(user)
            otp_code = generate_otp(user, 'login')
            send_otp_to_email(user, otp_code, 'login')
            
            return Response({
                "message": "Welcome back! Google login successful",
                "user_id": str(user.id),
                "tokens": tokens,
                "user_created": False,
                "user_info": {
                    "email": email,
                    "name": user.full_name,
                    "profile_photo_url": user.profile_photo_url,
                }
            })
                
        except CustomUser.DoesNotExist:
            # User doesn't exist - create new user using serializer
            try:
                # Generate a unique phone number for Google users
                import time
                temp_phone = f"google_{int(time.time())}"
                
                # Ensure phone number is unique
                counter = 1
                original_phone = temp_phone
                while CustomUser.objects.filter(phone_number=temp_phone).exists():
                    temp_phone = f"{original_phone}_{counter}"
                    counter += 1
                
                # Prepare data for serializer
                user_data = {
                    'phone_number': temp_phone,
                    'email': email,
                    'full_name': name,
                    'user_type': 'worker',  # Default user type
                    'password': 'google_oauth_user'  # Temporary password since it's OAuth
                }
                
                # Use your serializer to create the user
                serializer = RegisterUserSerializer(data=user_data)
                if serializer.is_valid():
                    user = serializer.save()
                    
                    # Update additional fields not in serializer
                    user.profile_photo_url = picture
                    user.email_verified = True  # Email is verified by Google
                    user.save()
                    
                    # Generate tokens for new user
                    tokens = get_tokens_for_user(user)
                    otp_code = generate_otp(user, 'registration')
                    send_otp_to_email(user, otp_code, 'registration')
                    # Send OTP to email for verification
                    return Response({
                        "message": "Account created successfully! Google login successful",
                        "user_id": str(user.id),
                        "tokens": tokens,
                        "user_created": True,
                        "user_info": {
                            "email": email,
                            "name": name,
                            "profile_photo_url": picture,
                            "phone_number": temp_phone,
                        }
                    })
                else:
                    return Response({
                        "error": "Failed to create user",
                        "details": serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                
            except Exception as e:
                # Handle any creation errors
                return Response(
                    {"error": f"Failed to create user: {str(e)}"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

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
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
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
    
class UpdateUserProfileView(APIView):
        def put(self, request):
            if not request.user.is_authenticated:
                return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
            user = request.user
            data = request.data
            
            # Update user fields
            user.full_name = data.get("full_name", user.full_name)
            user.phone_number = data.get("phone_number", user.phone_number)
            user.profile_photo_url = data.get("profile_photo_url", user.profile_photo_url)
            
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
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class LogoutView(APIView):
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Invalidate the user's tokens
        try:
            RefreshToken.for_user(request.user)
            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class DeleteAccountView(APIView):
            def delete(self, request):
                if not request.user.is_authenticated:
                    return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
                
                user = request.user
                try:
                    user.delete()
                    return Response({"message": "Account deleted successfully"}, status=status.HTTP_200_OK)
                except Exception as e:
                    return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                

class VerifyEmailView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        otp_code = request.data.get('otp_code')
        otp_type = request.data.get('otp_type')
        
        try:         
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if validate_otp(user, otp_code, otp_type):
            user.email_verified = True
            user.save()
            return Response({"message": "Email verified successfully"})
        
        return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"error": "User with this email does not exist"}, status=status.HTTP_404_NOT_FOUND)
        
        otp_code = generate_otp(user, 'password_reset')
        send_otp_to_email(user, otp_code, 'password_reset')
        
        return Response({
            "message": "Password reset OTP sent to your email",
            "user_id": str(user.id)
        }, status=status.HTTP_200_OK)