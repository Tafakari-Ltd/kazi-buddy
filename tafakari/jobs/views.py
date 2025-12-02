from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from .models import Job, JobCategory, Skill
from .serializers import (
    FeaturedJobSerializer, JobListSerializer, JobDetailSerializer, 
    JobCreateUpdateSerializer
)


class JobListView(APIView):
    """
    GET /jobs/ - List/filter/search jobs with pagination
    """
    
    def get(self, request):
        try:
            # Base queryset - only active, approved, public jobs
            queryset = Job.objects.filter(
                status='active', 
                admin_approved=True,
                visibility='public'
            ).select_related('employer', 'category').prefetch_related('job_skills__skill')
            
            # Apply filters
            queryset = self._apply_filters(queryset, request.query_params)
            
            # Apply search
            search = request.query_params.get('search')
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search) |
                    Q(location_text__icontains=search)
                )
            
            # Apply ordering
            ordering = request.query_params.get('ordering', '-created_at')
            if ordering in ['-created_at', 'created_at', '-budget_min', 'budget_min', '-budget_max', 'budget_max']:
                queryset = queryset.order_by(ordering)
            
            # Pagination
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
            
            serializer = JobListSerializer(page_obj.object_list, many=True)
            
            return Response({
                'results': serializer.data,
                'count': paginator.count,
                'page': page,
                'total_pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to fetch jobs: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _apply_filters(self, queryset, params):
        """Apply custom filters to queryset"""
        
        # Filter by job type
        job_type = params.get('job_type')
        if job_type:
            queryset = queryset.filter(job_type=job_type)
        
        # Filter by urgency level
        urgency = params.get('urgency')
        if urgency:
            queryset = queryset.filter(urgency_level=urgency)
        
        # Filter by category
        category = params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Filter by skills
        skills = params.get('skills')
        if skills:
            skill_names = [s.strip() for s in skills.split(',')]
            queryset = queryset.filter(
                job_skills__skill__name__in=skill_names
            ).distinct()
        
        # Filter by location
        location = params.get('location')
        if location:
            queryset = queryset.filter(
                Q(location_text__icontains=location) | 
                Q(location__icontains=location)
            )
        
        # Filter by salary range
        salary_range = params.get('salary_range')
        if salary_range:
            try:
                min_salary, max_salary = map(int, salary_range.split('-'))
                queryset = queryset.filter(
                    budget_min__gte=min_salary,
                    budget_max__lte=max_salary
                )
            except (ValueError, TypeError):
                pass
        
        return queryset


class JobCreateView(APIView):
    """
    POST /jobs/ - Create a job posting (auth required)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Check if user has employer profile
        if not hasattr(request.user, 'employer_profile'):
            return Response({
                'error': 'Only employers can create job postings'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = JobCreateUpdateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            try:
                job = serializer.save()
                
                # Return created job details
                job_serializer = JobDetailSerializer(job)
                
                return Response({
                    'message': 'Job created successfully',
                    'job_id': str(job.id),
                    'job_data': job_serializer.data
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({
                    'error': f'Failed to create job: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JobDetailView(APIView):
    """
    GET /jobs/<id>/ - View specific job details
    """
    
    def get(self, request, id):
        try:
            job = get_object_or_404(
                Job.objects.select_related('employer', 'category').prefetch_related('job_skills__skill'),
                id=id
            )
            
            # Increment view count if not the job owner
            if not (hasattr(request.user, 'employer_profile') and 
                    request.user.is_authenticated and
                    request.user.employer_profile == job.employer):
                job.views_count += 1
                job.save(update_fields=['views_count'])
            
            serializer = JobDetailSerializer(job)
            
            return Response({
                'job_data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to fetch job details: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JobUpdateView(APIView):
    """
    PUT /jobs/<id>/ - Update job posting (auth required, owner only)
    """
    permission_classes = [IsAuthenticated]
    
    def put(self, request, id):
        try:
            job = get_object_or_404(Job, id=id)
            
            # Check if user is the job owner
            if not (hasattr(request.user, 'employer_profile') and 
                    request.user.employer_profile == job.employer):
                return Response({
                    'error': 'You can only update your own job postings'
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = JobCreateUpdateSerializer(
                job, 
                data=request.data, 
                context={'request': request},
                partial=True
            )
            
            if serializer.is_valid():
                updated_job = serializer.save()
                
                # Return updated job details
                job_serializer = JobDetailSerializer(updated_job)
                
                return Response({
                    'message': 'Job updated successfully',
                    'job_data': job_serializer.data
                }, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'error': f'Failed to update job: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JobDeleteView(APIView):
    """
    DELETE /jobs/<id>/ - Delete job posting (auth required, owner only)
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, id):
        try:
            job = get_object_or_404(Job, id=id)
            
            # Check if user is the job owner
            if not (hasattr(request.user, 'employer_profile') and 
                    request.user.employer_profile == job.employer):
                return Response({
                    'error': 'You can only delete your own job postings'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Soft delete by changing status
            job.status = 'cancelled'
            job.save()
            
            return Response({
                'message': 'Job deleted successfully',
                'job_id': str(job.id)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to delete job: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FeaturedJobsView(APIView):
    """
    GET /jobs/featured/ - List featured jobs
    """
    
    def get(self, request):
        try:
            featured_jobs = Job.objects.filter(
                is_featured=True,
                status='active',
                admin_approved=True,
                visibility='public'
            ).select_related('employer', 'category').prefetch_related('urgency_level','budget_min')
            
            serializer = FeaturedJobSerializer(featured_jobs, many=True)
            
            return Response({
                'featured_jobs': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Failed to fetch featured jobs: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)