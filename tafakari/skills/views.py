from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from .models import Skill, SkillCategory
from .serializers import SkillSerializer, SkillCategorySerializer

# Create SkillCategory
class CreateSkillCategoryAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = SkillCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)  # Set created_by
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Update SkillCategory
class UpdateSkillCategoryAPIView(APIView):
    permission_classes = [IsAdminUser]

    def put(self, request, category_id):
        try:
            category = SkillCategory.objects.get(id=category_id, is_active=True)
        except SkillCategory.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = SkillCategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            # Prevent updating created_by during edits
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# List SkillCategories (updated to show creator)
class SkillCategoryListAPIView(APIView):
    def get(self, request):
        categories = SkillCategory.objects.filter(is_active=True)
        serializer = SkillCategorySerializer(categories, many=True)
        return Response({'categories': serializer.data})

class SkillCategoryDetailAPIView(APIView):
    def get(self, request, category_id):
        try:
            category = SkillCategory.objects.get(id=category_id, is_active=True)
        except SkillCategory.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = SkillCategorySerializer(category)
        return Response({'category': serializer.data})
    
class DeleteSkillCategoryAPIView(APIView):
    permission_classes = [IsAdminUser]

    def delete(self, request, category_id):
        try:
            category = SkillCategory.objects.get(id=category_id, is_active=True)
        except SkillCategory.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if the authenticated user is the creator of the category
        if category.created_by != request.user:
            return Response({'error': 'You are not authorized to delete this category'}, status=status.HTTP_403_FORBIDDEN)

        category.is_active = False  # Soft delete
        category.save()
        return Response({'message': 'Category deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


# Create Skill
class CreateSkillAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SkillSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)  # Set created_by
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Update Skill
class UpdateSkillAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, skill_id):
        try:
            skill = Skill.objects.get(id=skill_id, is_active=True)
        except Skill.DoesNotExist:
            return Response({'error': 'Skill not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = SkillSerializer(skill, data=request.data, partial=True)
        if serializer.is_valid():
            # Prevent updating created_by during edits
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# List Skills (updated to show creator)
class SkillListAPIView(APIView):
    def get(self, request):
        skills = Skill.objects.filter(is_active=True).select_related('category', 'created_by')
        serializer = SkillSerializer(skills, many=True)
        return Response({'skills': serializer.data})

# Skill Detail (updated to show creator)
class SkillDetailAPIView(APIView):
    def get(self, request, skill_id):
        try:
            skill = Skill.objects.get(id=skill_id, is_active=True)
        except Skill.DoesNotExist:
            return Response({'error': 'Skill not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = SkillSerializer(skill)
        return Response({'skill': serializer.data})
    
# Delete Skill (no changes needed)
class DeleteSkillAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, skill_id):
        try:
            skill = Skill.objects.get(id=skill_id, is_active=True)
        except Skill.DoesNotExist:
            return Response({'error': 'Skill not found'}, status=status.HTTP_404_NOT_FOUND)

        skill.is_active = False  # Soft delete
        skill.save()
        return Response({'message': 'Skill deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

class DeleteSkillCategoryAPIView(APIView):
    permission_classes = [IsAdminUser]

    def delete(self, request, category_id):
        try:
            category = SkillCategory.objects.get(id=category_id, is_active=True)
        except SkillCategory.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

        category.is_active = False  # Soft delete
        category.save()
        return Response({'message': 'Category deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

    

# List Skills by Category (updated to show creator)

class SkillListByCategoryAPIView(APIView):
    def get(self, request, category_id):
        try:
            category = SkillCategory.objects.get(id=category_id, is_active=True)
        except SkillCategory.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

        skills = Skill.objects.filter(category=category, is_active=True).select_related('category', 'created_by')
        serializer = SkillSerializer(skills, many=True)
        return Response({'skills': serializer.data})


class SkillListByUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            skills = Skill.objects.filter(created_by=user_id, is_active=True).select_related('category', 'created_by')
            serializer = SkillSerializer(skills, many=True)
            return Response({'skills': serializer.data})
        except Skill.DoesNotExist:
            return Response({'error': 'No skills found for the user'}, status=status.HTTP_404_NOT_FOUND)

class MySkillsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        skills = Skill.objects.filter(created_by=request.user, is_active=True).select_related('category', 'created_by')
        serializer = SkillSerializer(skills, many=True)
        return Response({'skills': serializer.data})

class DeleteSkillAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, skill_id):
        try:
            skill = Skill.objects.get(id=skill_id, is_active=True)
        except Skill.DoesNotExist:
            return Response({'error': 'Skill not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if the authenticated user is the creator of the skill
        if skill.created_by != request.user:
            return Response({'error': 'You are not authorized to delete this skill'}, status=status.HTTP_403_FORBIDDEN)

        skill.is_active = False  # Soft delete
        skill.save()
        return Response({'message': 'Skill deleted successfully'}, status=status.HTTP_204_NO_CONTENT)