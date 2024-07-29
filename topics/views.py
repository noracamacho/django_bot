# topics/views.py
from django.shortcuts import get_object_or_404, get_list_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Topic
from .serializers import TopicSerializer


class AddTopicView(APIView):
    def post(self, request):
        serializer = TopicSerializer(data=request.data)
        serializer.is_valid(raise_exception=True) 
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

class ListTopicsView(APIView):
    def get(self, request):
        topics = get_list_or_404(Topic)
        serializer = TopicSerializer(topics, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class GetTopicView(APIView):
    def get(self, request, pk):
        topic = get_object_or_404(Topic, pk=pk)
        serializer = TopicSerializer(topic)
        return Response(serializer.data)
    
    
class UpdateTopicView(APIView):
    def put(self, request, pk):
        topic = get_object_or_404(Topic, pk=pk)
        serializer = TopicSerializer(topic, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class DeleteTopicView(APIView):
    def delete(self, request, pk):
        topic = get_object_or_404(Topic, pk=pk)
        topic.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)