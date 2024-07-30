# tasks/urls.py
from django.urls import path
from .views import CreateTaskView, ListTasksView, GetTaskView, UpdateTaskView, DeleteTaskView

urlpatterns = [
    path('create/', CreateTaskView.as_view(), name='add-task'),
    path('list/', ListTasksView.as_view(), name='list-tasks'),
    path('<int:pk>/', GetTaskView.as_view(), name='get-task'),
    path('<int:pk>/update/', UpdateTaskView.as_view(), name='update-task'),
    path('<int:pk>/delete/', DeleteTaskView.as_view(), name='delete-task'),
]
