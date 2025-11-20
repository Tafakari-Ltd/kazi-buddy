from django.urls import path
from .views import ApproveUserView,DeactivateUserView,AllJobsListView,ApproveJobView,PendingJobsListView,ListPendingUsersView,UpdateJobApplicationStatusView

urlpatterns = [
    path('users/<uuid:user_id>/approve/', ApproveUserView.as_view(), name='approve_user'),
    path('users/<uuid:user_id>/deactivate/', DeactivateUserView.as_view(), name='deactivate_user'),
    path('admin/jobs/', AllJobsListView.as_view(), name='all-jobs-list'),
    path('jobs/pending/', PendingJobsListView.as_view(), name='pending-jobs-list'),
    path('jobs/<uuid:job_id>/approve/', ApproveJobView.as_view(), name='approve-job'),
    path('users/pending/', ListPendingUsersView.as_view(), name='list-pending-users'),
    path('applications/<uuid:application_id>/status/', UpdateJobApplicationStatusView.as_view(), name='update-application-status'),
]

