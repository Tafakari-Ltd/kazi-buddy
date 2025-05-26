from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser
from .serializers import RegisterUserSerializer, LoginSerializer
from utils.views import get_tokens_for_user
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
import requests
from django.urls import reverse
from django.views import View
from django.shortcuts import render
import jwt
import json
import requests

User = CustomUser

# Create your views here.
class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User registered successfully",
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





# class GoogleLoginCallback(APIView):
#     def get(self, request):
#         code = request.GET.get('code')
#         if not code:
#             return Response({"error": "Authorization code not provided"}, status=status.HTTP_400_BAD_REQUEST)
        
#         # Exchange the authorization code for tokens
#         token_url = 'https://oauth2.googleapis.com/token'
#         data = {
#             'code': code,
#             'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
#             'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
#             'redirect_uri': settings.GOOGLE_OAUTH_CALLBACK_URL,
#             'grant_type': 'authorization_code',
#         }
        
#         response = requests.post(token_url, data=data)
#         token_data = response.json()
        
#         if 'id_token' in token_data:
#             # Decode the JWT token (without verification for now)
#             # In production, you should verify the token
#             decoded_token = jwt.decode(
#                 token_data['id_token'], 
#                 options={"verify_signature": False}
#             )
            
#             user_info = {
#                 'email': decoded_token.get('email'),
#                 'name': decoded_token.get('name'),
#                 'given_name': decoded_token.get('given_name'),
#                 'family_name': decoded_token.get('family_name'),
#                 'picture': decoded_token.get('picture'),
#                 'email_verified': decoded_token.get('email_verified'),
#             }
            
#             return Response({
#                 'user_info': user_info,
#                 'tokens': token_data
#             })
        
#         return Response({"error": "No id_token received"}, status=status.HTTP_400_BAD_REQUEST)




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
  