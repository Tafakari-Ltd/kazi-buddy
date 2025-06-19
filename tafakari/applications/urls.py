from django.urls import path
from .views import CreateJobApplicationView,MyJobApplicationListView,JobApplicationDetailView,SpecificJobApplicationListView,AllJobApplicationListView

urlpatterns = [
   
    path('<uuid:job_id>/apply/', CreateJobApplicationView.as_view(), name='create-job-application'),
    path('me/', MyJobApplicationListView.as_view(), name='my-job-applications'),
    path('<uuid:application_id>/', JobApplicationDetailView.as_view(), name='job-application-detail'),
    path('job/<uuid:job_id>/', SpecificJobApplicationListView.as_view(), name='specific-job-applications'),
    path('all/', AllJobApplicationListView.as_view(), name='all-job-applications'),

    
]