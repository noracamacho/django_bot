# topics/urls.py
from django.urls import path
from .views import ListTopicsView, AddTopicView, UpdateTopicView, DeleteTopicView, GetTopicView

urlpatterns = [
    path('list/', ListTopicsView.as_view(), name='list-topics'),
    path('create/', AddTopicView.as_view(), name='create-topic'),
    path('<int:pk>/', GetTopicView.as_view(), name='get-topic'),
    path('<int:pk>/update/', UpdateTopicView.as_view(), name='update-topic'),
    path('<int:pk>/delete/', DeleteTopicView.as_view(), name='delete-topic'),
]
