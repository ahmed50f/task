from django.shortcuts import render
from .models import CustomUser, UserProfile, Notification
from .serilaizers import (
    NotificationCreateSerializer, NotificationSerializer,
    CustomUserSerializer, ChangePasswordSerializer,
    RegisterSerializer, UserProfileSerializer, ResetPasswordSerializer
)
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from django.utils.translation import gettext_lazy as _
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.conf import settings
from django.utils.crypto import get_random_string
from django.db import transaction
import time

# ✅ Register View
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        try:
            with transaction.atomic():
                user = serializer.save()
                user.set_password(serializer.validated_data['password'])
                user.save()
                return Response({
                    'user': serializer.data,
                    'message': _('User registered successfully.'),
                }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                "detail": _("Registration failed."),
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ✅ Login View
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get("email")
    password = request.data.get("password")

    try:
        user = CustomUser.objects.get(email=email)

        if not user.is_active:
            return Response({"detail": _("Account is not active. Please verify your email address.")}, status=status.HTTP_400_BAD_REQUEST)

        if user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': _('Logged in successfully.'),
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_id': user.id,
                'phone': user.phone,
            }, status=status.HTTP_200_OK)
        else:
            return Response({"detail": _("Invalid email or password.")}, status=status.HTTP_401_UNAUTHORIZED)
    except CustomUser.DoesNotExist:
        return Response({"detail": _("User not found.")}, status=status.HTTP_404_NOT_FOUND)

# ✅ Logout View
@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request):
    try:
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": _("Refresh token is required.")}, status=status.HTTP_400_BAD_REQUEST)

        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"detail": _("Logged out successfully.")}, status=status.HTTP_200_OK)
    except Exception:
        return Response({"detail": _("Invalid token or already blacklisted.")}, status=status.HTTP_400_BAD_REQUEST)


# ✅ User Profile ViewSet
class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    # 👇 هنا شلنا user=... عشان مايتبعتش مرتين
    def perform_create(self, serializer):
        serializer.save()


# ✅ Custom User ViewSet
class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return CustomUser.objects.all()
        return CustomUser.objects.filter(id=user.id)


# ✅ Forgot Password (By Email)
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    email = request.data.get("email")
    if not email:
        return Response({"detail": _("Email is required.")}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return Response({"detail": _("User not found.")}, status=status.HTTP_404_NOT_FOUND)

    reset_attempts = cache.get(f"forgot_password_attempts_{email}", 0)
    wait_time = settings.WAIT_TIMES[min(reset_attempts, len(settings.WAIT_TIMES) - 1)]

    last_sent_time = cache.get(f"forgot_password_last_sent_{email}")
    current_time = time.time()

    if last_sent_time and (current_time - last_sent_time) < wait_time:
        remaining_time = int(wait_time - (current_time - last_sent_time))
        return Response({
            "detail": _("Please wait %(seconds)d seconds before requesting a new OTP.") % {"seconds": remaining_time},
            "wait_time": remaining_time
        }, status=429)

    new_otp = get_random_string(length=4, allowed_chars='0123456789')
    cache.set(f"forgot_password_otp_{email}", new_otp, timeout=settings.OTP_TIMEOUT)
    cache.set(f"forgot_password_last_sent_{email}", current_time, timeout=wait_time)
    cache.set(f"forgot_password_attempts_{email}", reset_attempts + 1, timeout=86400)

    

    return Response({
        "message": _("OTP generated for password reset."),
        "email": email,
        "wait_time": wait_time,
        "otp_preview": new_otp # فقط لأغراض الاختبار
    }, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    serializer = ResetPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data.get("email")
    otp = serializer.validated_data.get("otp")
    new_password = serializer.validated_data.get("new_password")

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return Response({"detail": _("User not found.")}, status=status.HTTP_404_NOT_FOUND)

    cached_otp = cache.get(f"forgot_password_otp_{email}")
    if cached_otp != otp:
        return Response({"detail": _("Invalid or expired OTP.")}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()

    # حذف بيانات OTP من الكاش بعد النجاح
    cache.delete(f"forgot_password_otp_{email}")
    cache.delete(f"forgot_password_attempts_{email}")
    cache.delete(f"forgot_password_last_sent_{email}")

    return Response({"detail": _("Password reset successfully.")}, status=status.HTTP_200_OK)

# ✅ Change Password
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response({"message": _("Password changed successfully.")}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ✅ Notification View
class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all().order_by('-created_at')
    serializer_class = NotificationSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Notification.objects.all().order_by('-created_at')
        return user.notifications.all().order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return NotificationCreateSerializer
        return NotificationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notification = serializer.save()
        return Response({
            "notification": NotificationSerializer(notification).data,
            "message": _("Notification created successfully.")
        }, status=status.HTTP_201_CREATED)
        
    