from django.urls import path 
from .views import (
    CreateSkillCategoryAPIView,
    UpdateSkillCategoryAPIView,
    SkillCategoryListAPIView,
    CreateSkillAPIView,
    UpdateSkillAPIView,
    SkillListAPIView,
    SkillDetailAPIView,
)



urlpatterns = [
    path('categories/', SkillCategoryListAPIView.as_view(), name='skill-category-list'),
    path('categories/create/', CreateSkillCategoryAPIView.as_view(), name='create-skill-category'),
    path('categories/<uuid:category_id>/update/', UpdateSkillCategoryAPIView.as_view(), name='update-skill-category'),
    
    path('list/', SkillListAPIView.as_view(), name='skill-list'),
    path('create/', CreateSkillAPIView.as_view(), name='create-skill'),
    path('<uuid:skill_id>/update/', UpdateSkillAPIView.as_view(), name='update-skill'),
    path('<uuid:skill_id>/', SkillDetailAPIView.as_view(), name='skill-detail'),
]