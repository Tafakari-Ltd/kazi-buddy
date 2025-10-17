from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from accounts.models import CustomUser
from .serializers import ApproveUserSerializer, UserStatusSerializer


class ApproveUserView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        #check if email is already verified
        try:
            if not user.email_verified:
                return Response({"error": "User email is not verified"}, status=status.HTTP_400_BAD_REQUEST)
        except AttributeError:
            return Response({"error": "User email verification status unknown"}, status=status.HTTP_400_BAD_REQUEST)

        if user.is_verified:
            return Response({"message": "User is already verified"}, status=status.HTTP_200_OK)

        user.is_verified = True
        user.updated_at = timezone.now()
        user.save()

        serializer = ApproveUserSerializer(user)
        return Response(
            {"message": "User approved successfully", "user": serializer.data},
            status=status.HTTP_200_OK
        )
    
class DeactivateUserView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if not user.is_active:
            return Response({"message": "User is already deactivated"}, status=status.HTTP_200_OK)

        user.is_active = False
        user.updated_at = timezone.now()
        user.save()

        serializer = UserStatusSerializer(user)
        return Response(
            {"message": "User deactivated successfully", "user": serializer.data},
            status=status.HTTP_200_OK
        )