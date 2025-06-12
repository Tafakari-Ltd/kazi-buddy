from .serializers import JobSerializer,JobCategorySerializer,JobSkillSerializer
from rest_framework import views, permissions
from .models import Job, JobCategory, JobSkill
from rest_framework.response import Response

#Job Categories endpoints

class JobCategoriesListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        categories = JobCategory.objects.all()
        serializer = JobCategorySerializer(categories, many=True)
        return Response(serializer.data)

class JobCategoryDetailView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, category_id):
        try:
            category = JobCategory.objects.get(pk=category_id)
            serializer = JobCategorySerializer(category)
            return Response(serializer.data)
        except JobCategory.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)
    
class CreateJobCategoryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = JobCategorySerializer(data=request.data)
        if serializer.is_valid():
            category = serializer.save()
            return Response(JobCategorySerializer(category).data, status=201)
        return Response(serializer.errors, status=400)

class UpdateJobCategoryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, category_id):
        try:
            category = JobCategory.objects.get(pk=category_id)
            serializer = JobCategorySerializer(category, data=request.data)
            if serializer.is_valid():
                updated_category = serializer.save()
                return Response(JobCategorySerializer(updated_category).data)
            return Response(serializer.errors, status=400)
        except JobCategory.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)

class DeleteJobCategoryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, category_id):
        try:
            category = JobCategory.objects.get(pk=category_id)
            category.delete()
            return Response({"message": "Category deleted successfully"}, status=204)
        except JobCategory.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)

class JobsInCategoryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, category_id):
        try:
            category = JobCategory.objects.get(pk=category_id)
            jobs = category.jobs.all()
            serializer = JobSerializer(jobs, many=True)
            return Response(serializer.data)
        except JobCategory.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)


#job endpoints
class JobListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        jobs = Job.objects.all()
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data)
    

class JobDetailView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, job_id):
        try:
            job = Job.objects.get(pk=job_id)
            serializer = JobSerializer(job)
            return Response(serializer.data)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=404)
        

class CreateJobView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = JobSerializer(data=request.data)
        if serializer.is_valid():
            job = serializer.save(employer=request.user.employer_profile)
            return Response(JobSerializer(job).data, status=201)
        return Response(serializer.errors, status=400)
    

class UpdateJobView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, job_id):
        try:
            job = Job.objects.get(pk=job_id)
            serializer = JobSerializer(job, data=request.data)
            if serializer.is_valid():
                updated_job = serializer.save()
                return Response(JobSerializer(updated_job).data)
            return Response(serializer.errors, status=400)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=404)
        

class DeleteJobView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, job_id):
        try:
            job = Job.objects.get(pk=job_id)
            job.delete()
            return Response({"message": "Job deleted successfully"}, status=204)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=404)

class JobSkillsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, job_id):
        try:
            job = Job.objects.get(pk=job_id)
            job_skills = job.job_skills.all()
            serializer = JobSkillSerializer(job_skills, many=True)
            return Response(serializer.data)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=404)

class UpdateJobStatusView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, job_id):
        try:
            job = Job.objects.get(pk=job_id)
            status = request.data.get('status')
            if status not in [choice[0] for choice in Job.Status.choices]:
                return Response({"error": "Invalid status"}, status=400)
            job.status = status
            job.save()
            return Response(JobSerializer(job).data)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=404)


class JobsByEmployerView(views.APIView):
        permission_classes = [permissions.IsAuthenticated]

        def get(self, request):
            employer_id = request.query_params.get('employer_id')
            if not employer_id:
                return Response({"error": "Employer ID is required"}, status=400)
            try:
                jobs = Job.objects.filter(employer__id=employer_id)
                serializer = JobSerializer(jobs, many=True)
                return Response(serializer.data)
            except Job.DoesNotExist:
                return Response({"error": "No jobs found for the given employer"}, status=404)
        
class ListJobsByCategoryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, category_id):
        try:
            category = JobCategory.objects.get(pk=category_id)
            jobs = category.jobs.all()
            serializer = JobSerializer(jobs, many=True)
            return Response(serializer.data)
        except JobCategory.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)

class ListJobsByFilterView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        filters = {}
        for key in ['job_type', 'urgency_level', 'payment_type', 'status', 'visibility']:
            value = request.query_params.get(key)
            if value:
                filters[key] = value
        jobs = Job.objects.filter(**filters)
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data)
    
#job skills endpoints
class JobSkillsListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        job_skills = JobSkill.objects.all()
        serializer = JobSkillSerializer(job_skills, many=True)
        return Response(serializer.data)
    
class JobSkillDetailView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, skill_id):
        try:
            job_skill = JobSkill.objects.get(pk=skill_id)
            serializer = JobSkillSerializer(job_skill)
            return Response(serializer.data)
        except JobSkill.DoesNotExist:
            return Response({"error": "Job skill not found"}, status=404)
        
class CreateJobSkillView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = JobSkillSerializer(data=request.data)
        if serializer.is_valid():
            job_skill = serializer.save()
            return Response(JobSkillSerializer(job_skill).data, status=201)
        return Response(serializer.errors, status=400)
    
class UpdateJobSkillView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, skill_id):
        try:
            job_skill = JobSkill.objects.get(pk=skill_id)
            serializer = JobSkillSerializer(job_skill, data=request.data)
            if serializer.is_valid():
                updated_job_skill = serializer.save()
                return Response(JobSkillSerializer(updated_job_skill).data)
            return Response(serializer.errors, status=400)
        except JobSkill.DoesNotExist:
            return Response({"error": "Job skill not found"}, status=404)
        
class DeleteJobSkillView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, skill_id):
        try:
            job_skill = JobSkill.objects.get(pk=skill_id)
            job_skill.delete()
            return Response({"message": "Job skill deleted successfully"}, status=204)
        except JobSkill.DoesNotExist:
            return Response({"error": "Job skill not found"}, status=404)

