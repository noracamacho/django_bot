# bot_project/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/paths/', include('paths.urls')),
    path('api/topics/', include('topics.urls')),
]
