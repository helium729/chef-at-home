"""
URL configuration for familychef project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.http import JsonResponse
from django.urls import include, path
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static

from core.views import home, chef_board, pantry, shopping_list_view, pwa_manifest


def api_health_check(request):
    """Simple health check endpoint"""
    return JsonResponse({"status": "ok", "message": "FamilyChef API is running", "version": "1.0.0"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
    path("api/health/", api_health_check, name="api_health"),
    path("api-auth/", include("rest_framework.urls")),
    path("auth/", include("allauth.urls")),
    # PWA template views
    path("", home, name="home"),
    path("chef/", chef_board, name="chef_board"),
    path("pantry/", pantry, name="pantry"),
    path("shopping/", shopping_list_view, name="shopping_list"),
    path("manifest.json", pwa_manifest, name="pwa_manifest"),
]

# Add static files serving for development/testing
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
