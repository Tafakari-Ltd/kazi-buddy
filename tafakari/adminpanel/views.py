from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404
from accounts.models import CustomUser
from jobs.models import Job
from jobs.serializers import JobSerializer
from .serializers import ApproveUserSerializer, UserStatusSerializer
from rest_framework import status
from applications.models import JobApplication
from applications.serializers import JobApplicationSerializer
from rest_framework.permissions import IsAdminUser
from utils.custom_error import error_response
from utils.custom_pagination import CustomPagination
from employers.models import EmployerProfile
from employers.serializers import EmployerProfileSerializer



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

        # Atomic: is_verified + updated_at must update together
        with transaction.atomic():
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

        # Atomic: is_active + updated_at must update together
        with transaction.atomic():
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
    permission_classes = [permissions.IsAdminUser]
    
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
    permission_classes = [permissions.IsAdminUser]
    
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
    permission_classes = [permissions.IsAdminUser]
    
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
    
class ListPendingUsersView(APIView):
    permission_classes = [permissions.IsAdminUser]
    def get(self, request):
        users = CustomUser.objects.filter(is_verified=False)
        user_data = []
        
        for user in users:
            user_data.append({
                "user_id": str(user.id),
                "email": user.email,
                "phone_number": user.phone_number,
                "user_type": user.user_type,
                "full_name": user.full_name,
                "profile_photo_url": user.profile_photo_url,
                "email_verified": user.email_verified,
                "phone_verified": user.phone_verified,
            })
        
        return Response(user_data, status=status.HTTP_200_OK)

class UpdateJobApplicationStatusView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, application_id):
        try:
            application = JobApplication.objects.get(id=application_id)
        except JobApplication.DoesNotExist:
            return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get("status")
        if not new_status:
            return Response({"error": "'status' is required"}, status=status.HTTP_400_BAD_REQUEST)

        valid_statuses = [choice[0] for choice in JobApplication.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response({"error": f"Invalid status. Valid statuses: {valid_statuses}"}, status=status.HTTP_400_BAD_REQUEST)

        if application.status == new_status:
            return Response(
                {"message": "Status unchanged", "application": {"id": str(application.id), "status": application.status}},
                status=status.HTTP_200_OK
            )

        # Optional notes that may accompany the status update
        employer_notes = request.data.get("employer_notes")
        worker_notes = request.data.get("worker_notes")

        # Atomic: status + timestamps + notes must all update together;
        # select_for_update prevents concurrent admin status changes
        with transaction.atomic():
            application = JobApplication.objects.select_for_update().get(id=application_id)
            application.status = new_status

            # Set timestamps based on transition
            if application.status != "pending" and application.reviewed_at is None:
                application.reviewed_at = timezone.now()

            # Mark responded_at for decisive outcomes
            if application.status in ("accepted", "rejected", "withdrawn"):
                application.responded_at = timezone.now()
            else:
                application.responded_at = None

            if employer_notes is not None:
                application.employer_notes = employer_notes
            if worker_notes is not None:
                application.worker_notes = worker_notes

            application.save()

        # Use the JobApplicationSerializer for the response representation
        serializer = JobApplicationSerializer(application, context={"request": request})

        return Response(
            {"message": "Application status updated successfully", "application": serializer.data},
            status=status.HTTP_200_OK
        )


class DeleteAllUsersView(APIView):
    # permission_classes = [permissions.IsAdminUser]
    def delete(self, request):
        try:
            CustomUser.objects.all().delete()
            return Response({"message": "All users deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return error_response(
                message="Error deleting all users",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 

class GetAllUsersView(APIView):
    permission_classes = [permissions.IsAdminUser]
    def get(self, request):
        users = CustomUser.objects.all()
        user_data = []
        
        for user in users:
            user_data.append({
                "user_id": str(user.id),
                "email": user.email,
                "phone_number": user.phone_number,
                "user_type": user.user_type,
                "full_name": user.full_name,
                "profile_photo_url": user.profile_photo_url,
                "email_verified": user.email_verified,
                "phone_verified": user.phone_verified,
            })
        
        return Response(user_data, status=status.HTTP_200_OK)

#delete user by email endpoint 
class DeleteUserByEmailView(APIView):
    permission_classes = [permissions.IsAdminUser]
    def delete(self, request, email):
        try:
            user = CustomUser.objects.get(email=email)
            user.delete()
            return Response({"message": f"User with email {email} deleted successfully"}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return error_response(
                message="User not found",
                errors={"error": f"No user found with email {email}"},
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                message="Error deleting user",
                errors={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
class ListEmployerProfilesView(APIView):
    permission_classes = [permissions.IsAdminUser]
    pagination_class = CustomPagination

    def get(self, request):
        company_name = request.GET.get("company_name")
        location = request.GET.get("location")
        industry = request.GET.get("industry")
        business_type = request.GET.get("business_type")

        employers = EmployerProfile.objects.all()

        if company_name:
            employers = employers.filter(company_name__icontains=company_name)
        if location:
            employers = employers.filter(location__icontains=location)
        if industry:
            employers = employers.filter(industry__icontains=industry)
        if business_type:
            employers = employers.filter(business_type=business_type)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(employers, request, view=self)
        if page is not None:
            serializer = EmployerProfileSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = EmployerProfileSerializer(employers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
