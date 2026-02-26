from django.shortcuts import render
from .serializers import JobApplicationSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from jobs.models import Job
from .models import JobApplication
from workers.models import WorkerProfile
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .utils import check_if_user_isOwner
from utils.custom_pagination import CustomPagination
from django.db import transaction


# Create your views here.
class CreateJobApplicationView(APIView):
    """
    View to create a new job application.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = JobApplicationSerializer

    def post(self, request, *args, **kwargs):
        # Get the job_id from the URL parameters
        job_id = kwargs.get('job_id')
        if not job_id:
            return Response({
                'status': 'error',
                'message': 'Job ID is required.'
            }, status=400)

        # Atomic: duplicate check + application creation must be atomic to prevent
        # race conditions where two workers could simultaneously create duplicate applications
        with transaction.atomic():
            # Lock the job row to prevent concurrent application count issues
            try:
                job = Job.objects.select_for_update().get(id=job_id)
            except Job.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Job not found.'
                }, status=404)

            # Check if the worker has already applied for the job
            worker = request.user
            worker_profile = WorkerProfile.objects.filter(user=worker).first()
            if not worker_profile:
                return Response({
                    'status': 'error',
                    'message': 'Worker profile not found,you need to create a  profile before applying for jobs.'
                }, status=404)
            if JobApplication.objects.filter(job=job, worker=worker_profile).exists():
                return Response({
                    'status': 'error',
                    'message': 'You have already applied for this job.'
                }, status=400)

            serializer = self.serializer_class(data=request.data, context={'request': request})
            if serializer.is_valid():
                application = serializer.save(job=job, worker=worker_profile)
                return Response({
                    'status': 'success',
                    'message': 'Job application created successfully.',
                    'application_id': str(application.id),
                    'user': {
                        'id': str(application.worker.id),
                        'name': application.worker.user.full_name,
                        'email': application.worker.user.email
                    }
                }, status=201)
            return Response({
                'status': 'error',
                'message': 'Failed to create job application.',
                'errors': serializer.errors
            }, status=400)
    
class MyJobApplicationListView(APIView):
    """
    View to list all job applications for a worker.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    serializer_class = JobApplicationSerializer

    def get(self, request, *args, **kwargs):
        worker_profile = WorkerProfile.objects.filter(user=request.user).first()
        if not worker_profile:
            return Response({
                'status': 'error',
                'message': 'Worker profile not found.'
            }, status=404)

        applications = JobApplication.objects.filter(worker=worker_profile)
        paginator = self.pagination_class()
        paginated_applications = paginator.paginate_queryset(applications, request)
        serializer = self.serializer_class(paginated_applications, many=True)
        return Response({
            'status': 'success',
            'applications': serializer.data
        }, status=200)

class JobApplicationDetailView(APIView):
    """
    View to retrieve, update, or delete a job application.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    serializer_class = JobApplicationSerializer

    def get(self, request, *args, **kwargs):
        application_id = kwargs.get('application_id')
        try:
            application = JobApplication.objects.get(id=application_id)
            paginator = self.pagination_class()
            paginated_application = paginator.paginate_queryset([application], request)
        except JobApplication.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Job application not found.'
            }, status=404)
        #check wheather the user is the owner of the application
        check_if_user_isOwner(request.user, application_id)
        serializer = self.serializer_class(paginated_application)
        return Response({
            'status': 'success',
            'application': serializer.data
        }, status=200)
    
    def put(self, request, *args, **kwargs):
        application_id = kwargs.get('application_id')
        #check wheather the application_id is provided
        if not application_id:
            return Response({
                'status': 'error',
                'message': 'Application ID is required.'
            }, status=400)
        #check wheather the user is the owner of the application
        check_if_user_isOwner(request.user, application_id)
        

        try:
            application = JobApplication.objects.get(id=application_id)
        except JobApplication.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Job application not found.'
            }, status=404)
        # only allow updating if only the status is pending

        if application.status != 'pending':
            return Response({
                'status': 'error',
                'message': 'You can only update applications with a status of pending.'
            }, status=400)
        
        
        serializer = self.serializer_class(application, data=request.data, partial=True)
        if serializer.is_valid():
            updated_application = serializer.save()
            return Response({
                'status': 'success',
                'message': 'Job application updated successfully.',
                'application': self.serializer_class(updated_application).data
            }, status=200)
        return Response({
            'status': 'error',
            'message': 'Failed to update job application.',
            'errors': serializer.errors
        }, status=400)
    
    def delete(self, request, *args, **kwargs):
        application_id = kwargs.get('application_id')
        #check wheather the application_id is provided
        if not application_id:
            return Response({
                'status': 'error',
                'message': 'Application ID is required.'
            }, status=400)

        #check wheather the user is the owner of the application
        check_if_user_isOwner(request.user, application_id)  
        
        # Check if the application exists
        try:
            application = JobApplication.objects.get(id=application_id)
        except JobApplication.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Job application not found.'
            }, status=404)

        application.delete()
        return Response({
            'status': 'success',
            'message': 'Job application deleted successfully.'
        }, status=204)

class SpecificJobApplicationListView(APIView):
    """
    View to list all job applications for a job.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    serializer_class = JobApplicationSerializer

    def get(self, request, *args, **kwargs):
        job_id = kwargs.get('job_id')
        if not job_id:
            return Response({
                'status': 'error',
                'message': 'Job ID is required.'
            }, status=400)

        # Check if the job exists
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Job not found.'
            }, status=404)
        
        paginator = self.pagination_class()
        applications = JobApplication.objects.filter(job=job)
        paginated_applications = paginator.paginate_queryset(applications, request)
        serializer = self.serializer_class(paginated_applications, many=True)
        return Response({
            'status': 'success',
            'applications': serializer.data
        }, status=200)

class AllJobApplicationListView(APIView):
    """
    View to list all job applications.
    """
    # permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    serializer_class = JobApplicationSerializer

    def get(self, request, *args, **kwargs):
        applications = JobApplication.objects.all()
        paginator = self.pagination_class()
        paginated_applications = paginator.paginate_queryset(applications, request)
        serializer = self.serializer_class(paginated_applications, many=True)
        return Response({
            'status': 'success',
            'applications': serializer.data
        }, status=200)