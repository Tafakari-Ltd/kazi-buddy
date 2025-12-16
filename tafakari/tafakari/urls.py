"""
URL configuration for tafakari project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from accounts.views import  GoogleLoginCallback, GoogleLogin,LoginPage

urlpatterns = [
    path('admin/', admin.site.urls),
    # Include the URLs from the accounts app
    path('api/accounts/', include('accounts.urls')),

    path('api/v1/auth/', include('dj_rest_auth.urls')),
    path("auth/google/login/", LoginPage.as_view(), name="login"),

    re_path(r"^api/v1/auth/accounts/", include("allauth.urls")),

    path("api/v1/auth/registration/", include("dj_rest_auth.registration.urls")),
    #google auth urls
    path('api/v1/auth/google/', GoogleLogin.as_view(), name='google_login'),
    path('api/v1/auth/google/callback/', GoogleLoginCallback.as_view(), name='google_callback'),
    # Include the URLs from the workers app
    path('api/workers/', include('workers.urls')),
    # Include the URLs from the employers app
    path('api/employers/', include('employers.urls')),
    # Include the URLs from the jobs app
    path('api/jobs/', include('jobs.urls')),
    # Include the URLs from the skills app
    path('api/skills/', include('skills.urls')),
    path('api/applications/', include('applications.urls')),
    path('api/messages/', include('messaging.urls')),
    path('api/adminpanel/', include('adminpanel.urls')),

]