from rest_framework import viewsets, permissions
from .models import Task, SubTask
from .serializers import TaskSerializer, SubTaskSerializer
from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import gettext as _
from rest_framework.exceptions import NotFound



class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

   
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": _("Deleted successfully.")}, 
            status=status.HTTP_200_OK
        )


class SubTaskViewSet(viewsets.ModelViewSet):
    queryset = SubTask.objects.all()
    serializer_class = SubTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SubTask.objects.filter(task__user=self.request.user)

    def perform_create(self, serializer):
        task = serializer.validated_data.get('task')
        if task.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You cannot add a subtask to another user's task.")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": _("Deleted successfully.")}, 
            status=status.HTTP_200_OK
        )
