from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import random
import string
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import BaseUserManager
# Create your models here.
# Manager
from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, phone=None, **extra_fields):
        """Create and save a regular user with email and optional phone."""
        if not email:
            raise ValueError(_("The email must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, phone=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email=email, password=password, phone=phone, **extra_fields)


class CustomUser(AbstractUser):
    username = None  # remove username field
    phone = models.CharField(max_length=15, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=150, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # no extra required fields when creating superuser

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    
class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"
    
class OTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("User"))
    code = models.CharField(_("Code"), max_length=4, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    is_used = models.BooleanField(_("Is Used"), default=False)

    class Meta: 
        indexes = [
            models.Index(fields=["user", "created_at"]),
        ]
        verbose_name = _("OTP")
        verbose_name_plural = _("OTPs")

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = ''.join(random.choices(string.digits, k=4))
        super().save(*args, **kwargs)

    def clean(self):
        if not self.code.isdigit():
            raise ValidationError(_("The code must be digits only."))
        if len(self.code) != 4:
            raise ValidationError(_("The code must be exactly 4 digits."))
    
    def __str__(self):
        return f"{self.user.email} - {self.code}"


User = get_user_model()
class Notification(models.Model):
    title = models.CharField(_("Title"), max_length=255)
    message = models.TextField(_("Message"))
    recipients = models.ManyToManyField(User, related_name="notifications", verbose_name=_("Recipients"))
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    read = models.BooleanField(_("Read"), default=False)

    def __str__(self):
        return f"{self.title} ({self.created_at})"

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
    
    def send_global_notification(title, message):
        notification = Notification.objects.create(title=title, message=message)
        users = User.objects.all()
        notification.recipients.set(users)
        notification.save()
        return notification
    
    def send_user_notification(user, title, message):
        notification = Notification.objects.create(title=title, message=message)
        notification.recipients.add(user)
        notification.save()
        return notification