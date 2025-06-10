from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import EmployerProfile
from .serializers import EmployerProfileSerializer

class CreateEmployerProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Check if an employer profile already exists for the user
        if EmployerProfile.objects.filter(user=request.user).exists():
            return Response({"error": "Employer profile already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = EmployerProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RetrieveEmployerProfileView(APIView):
    def get(self, request, id):
        try:
            employer = EmployerProfile.objects.get(id=id)
            serializer = EmployerProfileSerializer(employer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except EmployerProfile.DoesNotExist:
            return Response({"error": "Employer profile not found"}, status=status.HTTP_404_NOT_FOUND)


class UpdateEmployerProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        try:
            employer = EmployerProfile.objects.get(id=id)
            if employer.user != request.user:
                return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
            serializer = EmployerProfileSerializer(employer, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except EmployerProfile.DoesNotExist:
            return Response({"error": "Employer profile not found"}, status=status.HTTP_404_NOT_FOUND)


class ListEmployerProfilesView(APIView):
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

        serializer = EmployerProfileSerializer(employers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
