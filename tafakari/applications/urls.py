from django.urls import path
from .views import CreateJobApplicationView

urlpatterns = [
   
    path('applications/<uuid:job_id>/create/', CreateJobApplicationView.as_view(), name='create-job-application'),
    
]