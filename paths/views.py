# paths/views.py
from django.shortcuts import get_object_or_404, get_list_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Path
from .serializers import PathSerializer


class ListPathsView(APIView):
    def get(self, request, format=None):
        paths = get_list_or_404(Path)
        serializer = PathSerializer(paths, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdatePathView(APIView):
    def put(self, request, pk, format=None):
        path = get_object_or_404(Path, pk=pk)
        serializer = PathSerializer(path, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class DeletePathView(APIView):
    def delete(self, request, pk, format=None):
        path = get_object_or_404(Path, pk=pk)
        path.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AddPathView(APIView):
    def post(self, request, format=None):
        serializer = PathSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GetPathView(APIView):
    def get(self, request, pk, format=None):
        path = get_object_or_404(Path, pk=pk)
        serializer = PathSerializer(path)
        return Response(serializer.data)
