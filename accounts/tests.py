from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import CustomUser, UserProfile, Notification


class AuthTests(APITestCase):

    def setUp(self):
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')
        self.change_password_url = reverse('accounts:change-password')

        self.user_data = {
            "email": "testuser@example.com",
            "phone": "0100000000",
            "password": "testpass123",
            "password2": "testpass123",
            "name": "Test User"
        }

    def test_register_user(self):
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CustomUser.objects.filter(email=self.user_data["email"]).exists())

    def test_login_user(self):
        # Create user manually
        user = CustomUser.objects.create_user(
            email="login@example.com",
            phone="0101111111",
            password="loginpass123"
        )
        data = {"email": "login@example.com", "password": "loginpass123"}  # ✅ login بالـ email
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)


class ProfileTests(APITestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="profile@example.com",
            phone="0102222222",
            password="profilepass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_user_profile(self):
        url = reverse('accounts:profiles-list')  # ✅ namespace + basename
        data = {"full_name": "Ahmed Mohamed", "bio": "Hello bio"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())


class NotificationTests(APITestCase):

    def setUp(self):
        self.admin_user = CustomUser.objects.create_superuser(
            email="admin@example.com",
            phone="0103333333",
            password="adminpass123"
        )
        self.client.force_authenticate(user=self.admin_user)

    def test_create_notification(self):
        url = reverse('accounts:notifications-list')  # ✅ namespace + basename
        data = {"title": "System Update", "message": "New update is available."}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Notification.objects.filter(title="System Update").exists())
