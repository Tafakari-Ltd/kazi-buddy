from django.urls import path
from .views import ApproveUserView,DeactivateUserView

urlpatterns = [
    path('users/<uuid:user_id>/approve/', ApproveUserView.as_view(), name='approve_user'),
    path('users/<uuid:user_id>/deactivate/', DeactivateUserView.as_view(), name='deactivate_user'),
]
