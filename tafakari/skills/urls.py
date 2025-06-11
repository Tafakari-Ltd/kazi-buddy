from django.urls import path 
from .views import (
    CreateSkillCategoryAPIView,
    UpdateSkillCategoryAPIView,
    SkillCategoryListAPIView,
    CreateSkillAPIView,
    UpdateSkillAPIView,
    SkillListAPIView,
    SkillDetailAPIView,
    SkillCategoryDetailAPIView,
    DeleteSkillCategoryAPIView,
    DeleteSkillAPIView,
    SkillListByUserAPIView,
    SkillListByCategoryAPIView,
    MySkillsAPIView,

)



urlpatterns = [
    path('categories/', SkillCategoryListAPIView.as_view(), name='skill-category-list'),
    path('categories/create/', CreateSkillCategoryAPIView.as_view(), name='create-skill-category'),
    path('categories/<uuid:category_id>/update/', UpdateSkillCategoryAPIView.as_view(), name='update-skill-category'),
    path('categories/<uuid:category_id>/', SkillCategoryDetailAPIView.as_view(), name='skill-category-detail'),
    path('categories/<uuid:category_id>/delete/', DeleteSkillCategoryAPIView.as_view(), name='delete-skill-category'),
    
    path('list/', SkillListAPIView.as_view(), name='skill-list'),
    path('create/', CreateSkillAPIView.as_view(), name='create-skill'),
    path('<uuid:skill_id>/update/', UpdateSkillAPIView.as_view(), name='update-skill'),
    path('<uuid:skill_id>/', SkillDetailAPIView.as_view(), name='skill-detail'),
    path('<uuid:skill_id>/delete/', DeleteSkillAPIView.as_view(), name='delete-skill'),
    path('categories/<uuid:category_id>/skills/', SkillListAPIView.as_view(), name='category-skill-list'),
    path('category/<uuid:category_id>/list/', SkillListByCategoryAPIView.as_view(), name='skill-list-by-category'),
    path('users/<uuid:user_id>/', SkillListByUserAPIView.as_view(), name='skill-list-by-user'),
    path('my-skills/', MySkillsAPIView.as_view(), name='my-skills'),
]