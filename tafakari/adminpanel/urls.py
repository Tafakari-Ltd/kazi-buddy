from django.urls import path
from .views import ApproveUserView,DeactivateUserView,AllJobsListView,ApproveJobView,PendingJobsListView

urlpatterns = [
    path('users/<uuid:user_id>/approve/', ApproveUserView.as_view(), name='approve_user'),
    path('users/<uuid:user_id>/deactivate/', DeactivateUserView.as_view(), name='deactivate_user'),
    path('admin/jobs/', AllJobsListView.as_view(), name='all-jobs-list'),
    path('jobs/pending/', PendingJobsListView.as_view(), name='pending-jobs-list'),
    path('jobs/<uuid:job_id>/approve/', ApproveJobView.as_view(), name='approve-job'),
]

