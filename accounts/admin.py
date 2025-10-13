from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, UserProfile, OTP, Notification


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ("id", "phone", "email", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff")
    search_fields = ("phone", "email")
    ordering = ("id",)

    fieldsets = (
        (None, {"fields": ("phone", "email", "password")}),
        (_("Personal Information"), {"fields": ("first_name", "last_name")}),
        (_("Permissions"), {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")
        }),
        (_("Important Dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone", "email", "password1", "password2", "is_active", "is_staff"),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "full_name")
    search_fields = ("full_name", "user__email", "user__phone")

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "code", "created_at", "is_used")
    list_filter = ("is_used", "created_at")
    search_fields = ("user__email", "user__phone", "code")
    readonly_fields = ("created_at",)

    class Meta:
        verbose_name = _("OTP")
        verbose_name_plural = _("OTPs")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "get_recipients", "created_at", "read")
    list_filter = ("read", "created_at")
    search_fields = ("title", "message", "recipients__email")
    actions = ["send_to_all"]
    readonly_fields = ("created_at",)

    def get_recipients(self, obj):
        return ", ".join([user.email for user in obj.recipients.all()])
    get_recipients.short_description = _("Recipients")

    def send_to_all(self, request, queryset):
        for notification in queryset:
            notification.recipients.set(CustomUser.objects.all())
        self.message_user(request, _("Recipients set to all users."))
    send_to_all.short_description = _("Send selected notifications to all users")

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")


# Register Custom User
admin.site.register(CustomUser, CustomUserAdmin)
