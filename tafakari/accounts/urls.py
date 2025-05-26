from django.urls import path
from .views import LoginView, RegisterView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # User registration and login endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),

    # Token refresh endpoint
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]

