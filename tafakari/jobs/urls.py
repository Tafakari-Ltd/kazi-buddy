from django.urls import path
from . import views

urlpatterns = [
    path('jobs/', views.JobListView.as_view(), name='job-list'),
    path('jobs/create/', views.JobCreateView.as_view(), name='job-create'),
    path('jobs/<uuid:id>/', views.JobDetailView.as_view(), name='job-detail'),
    path('jobs/<uuid:id>/update/', views.JobUpdateView.as_view(), name='job-update'),
    path('jobs/<uuid:id>/delete/', views.JobDeleteView.as_view(), name='job-delete'),
]