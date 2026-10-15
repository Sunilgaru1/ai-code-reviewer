"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path, include
from django.http import JsonResponse

def health_check(request):
    """
    A simple root URL response. Cloud providers (Render, AWS) ping this 
    to verify the app is alive and healthy.
    """
    return JsonResponse({
        "status": "online",
        "app": "AI Code Reviewer Engine",
        "version": "1.0.0"
    })

urlpatterns = [
    path('', health_check, name='home'),
    path('admin/', admin.site.urls),
    path("webhooks/", include("webhooks.urls")),
]
