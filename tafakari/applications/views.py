from django.shortcuts import render
from .serializers import JobApplicationSerializer, WorkerInvitationSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from jobs.models import Job
from .models import JobApplication, WorkerInvitation

# Create your views here.
class CreateJobApplicationView(APIView):
    """
    View to create a new job application.
    """
    serializer_class = JobApplicationSerializer

    def post(self, request, *args, **kwargs):
        # Get the job_id from the URL parameters
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

        # Check if the worker has already applied for the job
        worker = request.user.workerprofile
        if JobApplication.objects.filter(job=job, worker=worker).exists():
            return Response({
                'status': 'error',
                'message': 'You have already applied for this job.'
            }, status=400)

        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            application = serializer.save(job=job, worker=worker)
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