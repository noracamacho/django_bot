# paths/urls.py
from django.urls import path
from .views import ListPathsView, UpdatePathView, DeletePathView, CreatePathView, GetPathView

urlpatterns = [
    path('list/', ListPathsView.as_view(), name='list-paths'),
    path('<int:pk>/update/', UpdatePathView.as_view(), name='update-path'),
    path('<int:pk>/delete/', DeletePathView.as_view(), name='delete-path'),
    path('create/', CreatePathView.as_view(), name='create-path'),
    path('<int:pk>/', GetPathView.as_view(), name='get-path'),
]
