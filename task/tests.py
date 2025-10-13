from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from accounts.models import CustomUser
from task.models import Task, SubTask


class TaskAPITestCase(APITestCase):
    def setUp(self):
        # إنشاء مستخدمين
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            phone="0100000000",
            password="12345678"
        )
        self.other_user = CustomUser.objects.create_user(
            email="other@example.com",
            phone="0111111111",
            password="12345678"
        )

        # تسجيل الدخول للمستخدم الأول
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # إنشاء مهمة أساسية
        self.task = Task.objects.create(
            user=self.user,
            title="Test Task",
            description="This is a test task"
        )

    def test_create_task(self):
        """يتأكد من إمكانية إنشاء مهمة جديدة"""
        url = reverse("task-list")
        data = {
            "title": "New Task",
            "description": "Description for new task"
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.filter(user=self.user).count(), 2)

    def test_get_tasks(self):
        """يتأكد من عرض المهام الخاصة بالمستخدم"""
        url = reverse("task-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], self.task.title)

    def test_update_task(self):
        """يتأكد من تعديل المهمة"""
        url = reverse("task-detail", args=[self.task.id])
        data = {"title": "Updated Title"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Updated Title")

    def test_delete_task(self):
        """يتأكد من حذف المهمة"""
        url = reverse("task-detail", args=[self.task.id])
        response = self.client.delete(url)
        # تعديل التحقق ليوافق الـ ViewSet الحالي
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], "Deleted successfully.")
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())

    def test_create_subtask(self):
        """يتأكد من إمكانية إضافة subtask داخل مهمة"""
        url = reverse("subtask-list")
        data = {
            "task": self.task.id,
            "title": "Subtask 1",
            "description": "This is a subtask",
            "completed": False
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SubTask.objects.filter(task=self.task).count(), 1)

    def test_cannot_add_subtask_to_other_user_task(self):
        """يتأكد من منع المستخدم من إضافة subtask لمهمة مستخدم تاني"""
        other_task = Task.objects.create(
            user=self.other_user,
            title="Other Task",
            description="Someone else's task"
        )
        url = reverse("subtask-list")
        data = {
            "task": other_task.id,
            "title": "Invalid Subtask",
            "description": "Should not be allowed",
            "completed": False
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(SubTask.objects.count(), 0)
