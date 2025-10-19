app_name = 'accounts'
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    register,
    login_view,
    logout,
    forgot_password,
    reset_password,
    change_password,
    UserProfileViewSet,
    CustomUserViewSet,
    NotificationViewSet,
)

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='users')
router.register(r'profiles', UserProfileViewSet, basename='profiles')
router.register(r'notifications', NotificationViewSet, basename='notifications')

urlpatterns = [
    # Auth
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout, name='logout'),
    
    # Password
    path('forgot-password/', forgot_password, name='forgot-password'),
    path('reset-password/', reset_password, name='reset-password'),
    path('change-password/', change_password, name='change-password'),

    # API routes via router
    path('', include(router.urls)),
]