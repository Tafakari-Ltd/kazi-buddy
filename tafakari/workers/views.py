from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ObjectDoesNotExist
from .models import WorkerProfile
import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import WorkerProfileSerializer
from rest_framework.views import APIView
from rest_framework import serializers
from django.db import IntegrityError
from .custom_error import error_response

class CreateWorkerProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if WorkerProfile.objects.filter(user=request.user).exists():
            return error_response(
                message="Worker profile already exists for this user",
                errors={"error": "Duplicate profile found"},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = WorkerProfileSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return error_response(
                    message="Database error occurred while creating profile",
                    errors={"error": "Integrity error"},
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return error_response(
            message="Invalid data",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
class ViewWorkerProfileView(APIView):
    def get(self, request, id):
        try:
            worker_profile = WorkerProfile.objects.get(id=id)
            serializer = WorkerProfileSerializer(worker_profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except WorkerProfile.DoesNotExist:
            return error_response(
                message="Worker profile not found",
                errors={"error": "No profile matches the given ID"},
                status_code=status.HTTP_404_NOT_FOUND
            )
class UpdateWorkerProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        try:
            worker_profile = WorkerProfile.objects.get(id=id)
            if worker_profile.user != request.user:
                return error_response(
                    message="You do not have permission to update this profile",
                    errors={"error": "Permission denied"},
                    status_code=status.HTTP_403_FORBIDDEN
                )

            serializer = WorkerProfileSerializer(worker_profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return error_response(
                message="Invalid data",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        except WorkerProfile.DoesNotExist:
            return error_response(
                message="Worker profile not found",
                errors={"error": "No profile matches the given ID"},
                status_code=status.HTTP_404_NOT_FOUND
            )
        


class ListWorkerProfilesView(APIView):
    def get(self, request):
        try:
            worker_profiles = WorkerProfile.objects.all()

            location = request.GET.get("location")
            availability = request.GET.get("availability")
            min_experience = request.GET.get("min_experience")
            max_experience = request.GET.get("max_experience")
            min_rate = request.GET.get("min_rate")
            max_rate = request.GET.get("max_rate")
            status_filter = request.GET.get("status")
            min_completion = request.GET.get("min_completion")

            if location:
                worker_profiles = worker_profiles.filter(location__icontains=location)
            if availability:
                worker_profiles = worker_profiles.filter(is_available=availability.lower() == "true")
            if min_experience:
                worker_profiles = worker_profiles.filter(years_experience__gte=int(min_experience))
            if max_experience:
                worker_profiles = worker_profiles.filter(years_experience__lte=int(max_experience))
            if min_rate:
                worker_profiles = worker_profiles.filter(hourly_rate__gte=float(min_rate))
            if max_rate:
                worker_profiles = worker_profiles.filter(hourly_rate__lte=float(max_rate))
            if status_filter:
                worker_profiles = worker_profiles.filter(verification_status=status_filter)
            if min_completion:
                worker_profiles = worker_profiles.filter(profile_completion_percentage__gte=int(min_completion))

            serializer = WorkerProfileSerializer(worker_profiles, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return error_response(
                message="An error occured when listing profiles",
                errors={"error":f"{str(e)}"},
                status_code = status.HTTP_400_BAD_REQUEST

            )
    
