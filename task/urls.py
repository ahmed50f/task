from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, SubTaskViewSet

router = DefaultRouter()
router.register(r'task', TaskViewSet, basename='task')        # 👈 متطابق مع reverse('task-list')
router.register(r'subtask', SubTaskViewSet, basename='subtask')  # 👈 متطابق مع reverse('subtask-list')

urlpatterns = router.urls
