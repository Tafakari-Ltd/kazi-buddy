from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from django.shortcuts import get_object_or_404
from accounts.models import CustomUser
from jobs.models import Job
from jobs.serializers import JobSerializer
from .serializers import ApproveUserSerializer, UserStatusSerializer


class ApproveUserView(APIView):
    # permission_classes = [permissions.IsAdminUser]

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
    # permission_classes = [permissions.IsAdminUser]

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
    



class AllJobsListView(APIView):
    """
    List all jobs regardless of approval status.
    Typically restricted to admin users.
    """
    # permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        jobs = Job.objects.all().order_by('-created_at')
        serializer = JobSerializer(jobs, many=True)
        return Response(
            {
                "message": "All jobs retrieved successfully",
                "data": serializer.data,
                "total": jobs.count()
            },
            status=status.HTTP_200_OK
        )


class ApproveJobView(APIView):
    """
    Approve a job by setting admin_approved to True.
    Only accessible by admin users.
    """
    # permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, job_id):
        job = get_object_or_404(Job, id=job_id)
        
        # Check if already approved
        if job.admin_approved:
            return Response(
                {
                    "message": "Job is already approved",
                    "data": JobSerializer(job).data
                },
                status=status.HTTP_200_OK
            )
        
        # Approve the job
        job.admin_approved = True
        job.save()
        
        return Response(
            {
                "message": "Job approved successfully",
                "data": JobSerializer(job).data
            },
            status=status.HTTP_200_OK
        )
    
    def delete(self, request, job_id):
        """
        Unapprove a job (set admin_approved to False).
        """
        job = get_object_or_404(Job, id=job_id)
        
        if not job.admin_approved:
            return Response(
                {
                    "message": "Job is already unapproved",
                    "data": JobSerializer(job).data
                },
                status=status.HTTP_200_OK
            )
        
        job.admin_approved = False
        job.save()
        
        return Response(
            {
                "message": "Job unapproved successfully",
                "data": JobSerializer(job).data
            },
            status=status.HTTP_200_OK
        )


class PendingJobsListView(APIView):
    """
    List all jobs pending approval (admin_approved=False).
    Only accessible by admin users.
    """
    # permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        jobs = Job.objects.filter(admin_approved=False).order_by('-created_at')
        serializer = JobSerializer(jobs, many=True)
        return Response(
            {
                "message": "Pending jobs retrieved successfully",
                "data": serializer.data,
                "total": jobs.count()
            },
            status=status.HTTP_200_OK
        )