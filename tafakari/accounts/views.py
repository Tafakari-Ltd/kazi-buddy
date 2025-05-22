from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser
from .serializers import RegisterSerializer, LoginSerializer
from utils.views import get_tokens_for_user

# Create your views here.
class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
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
