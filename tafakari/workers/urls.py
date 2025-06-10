from django.urls import path
from .views import CreateWorkerProfileView, ViewWorkerProfileView, UpdateWorkerProfileView, ListWorkerProfilesView
urlpatterns = [
    # Worker profile management endpoints
    path('profiles/', CreateWorkerProfileView.as_view(), name='create_worker_profile'),
    path('profiles/<uuid:id>/', ViewWorkerProfileView.as_view(), name='view_worker_profile'),
    path('profiles/<uuid:id>/update/', UpdateWorkerProfileView.as_view(), name='update_worker_profile'),
    path('profiles/list/', ListWorkerProfilesView.as_view(), name='list_worker_profiles'),
]