from .serializers import JobSerializer,JobCategorySerializer,JobSkillSerializer
from rest_framework import views, permissions
from .models import Job, JobCategory, JobSkill
from rest_framework.response import Response
from employers.models import EmployerProfile
from skills.models import Skill

#Job Categories endpoints

class JobCategoriesListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        categories = JobCategory.objects.all()
        serializer = JobCategorySerializer(categories, many=True)
        return Response(
            {
                "message": "Job categories retrieved successfully",
                "data": serializer.data
            },
            status=200
        )

class JobCategoryDetailView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, category_id):
        try:
            category = JobCategory.objects.get(pk=category_id)
            serializer = JobCategorySerializer(category)
            return Response(
                {
                    "message": "Job category retrieved successfully",
                    "data": serializer.data
                },
                status=200
            )
        except JobCategory.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)
    
class CreateJobCategoryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = JobCategorySerializer(data=request.data)
        if serializer.is_valid():
            category = serializer.save()
            return Response(
                {
                    "message": "Job category created successfully",
                    "data": JobCategorySerializer(category).data
                },
                status=201
            )
        return Response(serializer.errors, status=400)

class UpdateJobCategoryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, category_id):
        try:
            category = JobCategory.objects.get(pk=category_id)
            serializer = JobCategorySerializer(category, data=request.data)
            if serializer.is_valid():
                updated_category = serializer.save()
                return Response(
                    {
                        "message": "Job category updated successfully",
                        "data": JobCategorySerializer(updated_category).data
                    },
                    status=200
                )
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
            return Response(
                {
                    "message": "Jobs in category retrieved successfully",
                    "data": serializer.data
                },
                status=200
            )
        except JobCategory.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)


#job endpoints
class JobListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        jobs = Job.objects.all()
        serializer = JobSerializer(jobs, many=True)
        return Response(
            {
                "message": "Jobs retrieved successfully",
                "data": serializer.data
            },
            status=200
        )
    

class JobDetailView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, job_id):
        try:
            job = Job.objects.get(pk=job_id)
            serializer = JobSerializer(job)
            return Response(
                {
                    "message": "Job retrieved successfully",
                    "data": serializer.data
                },
                status=200
            )
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=404)
        

class CreateJobView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = JobSerializer(data=request.data)
        #chek wheather the category attribute is provided in the request data and if it is provided, check whether the category exists and if it exists, set the category attribute of the job to the category object
        if 'category' in request.data:
            try:
                category = JobCategory.objects.get(pk=request.data['category'])
                request.data['category'] = category.id
            except JobCategory.DoesNotExist:
                return Response({"error": "Category not found"}, status=404)
        
        # check wheather the authenticated user has an employer profile and get profile of the user 
        try:
            employer_profile = EmployerProfile.objects.get(user=request.user)
            request.data['employer'] = employer_profile.id
        except EmployerProfile.DoesNotExist:
            return Response({"error": "Employer profile not found"}, status=404)    
        if serializer.is_valid():
            job = serializer.save(employer=employer_profile,category=category)
            return Response(
                {
                    "message": "Job created successfully",
                    "data": JobSerializer(job).data
                },
                status=201
            )
        return Response(serializer.errors, status=400)
    

class UpdateJobView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, job_id):
        try:
            job = Job.objects.get(pk=job_id)
            serializer = JobSerializer(job, data=request.data)
            if serializer.is_valid():
                updated_job = serializer.save()
                return Response(
                    {
                        "message": "Job updated successfully",
                        "data": JobSerializer(updated_job).data
                    },
                    status=200
                )
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
            return Response(
                {
                    "message": "Job skills retrieved successfully",
                    "data": serializer.data
                },
                status=200
            )
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
            return Response(
                {
                    "message": "Job status updated successfully",
                    "data": JobSerializer(job).data
                },
                status=200
            )
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=404)


class JobsByEmployerView(views.APIView):
        permission_classes = [permissions.IsAuthenticated]

        def get(self, request):
            employer_id = request.query_params.get('employer_id')
            if not employer_id:
                return Response({"error": "Employer ID is required"}, status=400)
            try:
                jobs = Job.objects.filter(employer=employer_id)
                serializer = JobSerializer(jobs, many=True)
                return Response(
                    {
                        "message": f"Jobs  retrieved successfully for employer {jobs[0].employer.user.full_name if jobs else 'Unknown'}",
                        "data": serializer.data
                    },
                    status=200
                )
            except Job.DoesNotExist:
                return Response({"error": "No jobs found for the given employer"}, status=404)
        
class ListJobsByCategoryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, category_id):
        try:
            category = JobCategory.objects.get(pk=category_id)
            jobs = category.jobs.all()
            serializer = JobSerializer(jobs, many=True)
            return Response(
                {
                    "message": f"Jobs in category '{category.name}' retrieved successfully",
                    "data": serializer.data
                },
                status=200
            )
        except JobCategory.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)
        
#endpoint to get the employer who posted the job
class JobEmployerView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, job_id):
        try:
            job = Job.objects.get(pk=job_id)
            employer = job.employer
            return Response(
                {
                    "message": "Employer retrieved successfully",
                    "data": {
                        "id": employer.id,
                        "full_name": employer.user.full_name,
                        "email": employer.user.email
                    }
                },
                status=200
            )
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=404)

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
        return Response(
            {
                "message": "Filtered jobs retrieved successfully",
                "data": serializer.data
            },
            status=200
        )
    
#job skills endpoints
class JobSkillsListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        job_skills = JobSkill.objects.all()
        serializer = JobSkillSerializer(job_skills, many=True)
        return Response(
            {
                "message": "Job skills retrieved successfully",
                "data": serializer.data
            }
        )
    
class JobSkillDetailView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, skill_id):
        try:
            job_skill = JobSkill.objects.get(pk=skill_id)
            serializer = JobSkillSerializer(job_skill)
            return Response(
                {
                    "message": "Job skill retrieved successfully",
                    "data": serializer.data
                },
                status=200
            )
        except JobSkill.DoesNotExist:
            return Response({"error": "Job skill not found"}, status=404)
        
class CreateJobSkillView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request,job_id):
        # Check if the job exists
        try:
            job = Job.objects.get(pk=job_id)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=404)
        serializer = JobSkillSerializer(data=request.data)
        #check if the skill is provided in the request data and if it is provided, check whether the skill exists and if it exists, give a response that the skill already exists for the job
        if 'skill' in request.data:
            #check wheater the skill exists in the database and if not , tell the user to provide a valid skill
            try:
                skill = Skill.objects.get(name=request.data['skill'])
                
            except Skill.DoesNotExist:
                return Response({"error": "Skill not found in the database, it needs to be added"}, status=404)
           
            
            #check if the skill already exists for the job and if it exists, give a response that the skill already exists for the job
            try:
                skills = JobSkill.objects.filter(job=job)
                #check if the skill already exists for the job
                for skill in skills:
            
                        if skill.skill.name.lower().strip() == request.data['skill'].lower().strip():

                            return Response({"error": "Skill already exists for this job"}, status=400)
                        

            except JobSkill.DoesNotExist:
                pass
            
        if serializer.is_valid():
            job_skill = serializer.save(job=job)
            return Response(
                {
                    "message": "Job skill created successfully",
                    "data": JobSkillSerializer(job_skill).data
                }
            )
        return Response(serializer.errors, status=400)
    
class UpdateJobSkillView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, skill_id):
        try:
            job_skill = JobSkill.objects.get(pk=skill_id)
            serializer = JobSkillSerializer(job_skill, data=request.data)
            if serializer.is_valid():
                updated_job_skill = serializer.save()
                return Response(
                    {
                        "message": "Job skill updated successfully",
                        "data": JobSkillSerializer(updated_job_skill).data
                    },
                    status=200
                )
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

