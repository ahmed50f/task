from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, UserProfile, OTP , Notification
from django.contrib.auth import get_user_model


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'phone', 'date_joined', 'name']
        read_only_fields = ['id', 'date_joined']


class UserProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'full_name', 'bio', 'birth_date']
        read_only_fields = ['id', 'user']

    def create(self, validated_data):
        user = self.context['request'].user
        if not user.is_authenticated:
            raise serializers.ValidationError({"detail": _("Authentication required.")})
        profile = UserProfile.objects.create(user=user, **validated_data)
        return profile
    
    def update(self, instance, validated_data):
        instance.full_name = validated_data.get('full_name', instance.full_name)
        instance.bio = validated_data.get('bio', instance.bio)
        instance.birth_date = validated_data.get('birth_date', instance.birth_date)
        instance.save()
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True, required=False, label=_("Full Name"))
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, label=_("Password"))
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, label=_("Confirm Password"))

    class Meta:
        model = CustomUser
        fields = ['email', 'phone', 'password', 'password2', 'name']
        extra_kwargs = {
            'email': {'label': _("Email")},
            'phone': {'label': _("Phone")},
        }

    def validate(self, attrs):
        if not (6 <= len(attrs['password']) <= 16):
            raise serializers.ValidationError({"detail": _("Password must be between 6 and 16 characters.")})

        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": _("Passwords do not match.")})

        if CustomUser.objects.filter(phone=attrs['phone']).exists():
            raise serializers.ValidationError({"phone": _("Phone number is already in use.")})

        if CustomUser.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": _("Email address is already in use.")})

        return attrs

    def create(self, validated_data):
        name = validated_data.pop('name', None)
        validated_data.pop('password2')
        password = validated_data.pop('password')

        # إنشاء المستخدم
        user = CustomUser.objects.create_user(password=password, **validated_data)
        user.is_active = True
        user.save()

        # إنشاء UserProfile وربط الاسم فيه
        UserProfile.objects.create(user=user, full_name=name if name else "")

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(label=_("Email"), required=True)
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        required=True
    )
    remember_me = serializers.BooleanField(label=_("Remember Me"), required=False, default=False)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # تسجيل الدخول عن طريق الإيميل
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError({"detail": _("Invalid email or password.")})

            if not user.check_password(password):
                raise serializers.ValidationError({"detail": _("Invalid email or password.")})

            if not user.is_active:
                raise serializers.ValidationError({"detail": _("Account is not active. Please verify with OTP.")})

            attrs['user'] = user
            return attrs

        raise serializers.ValidationError({"detail": _("Both email and password are required.")})
    
# ✅ Serializer for Reset Password
class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(label=_("Email"))
    otp = serializers.CharField(max_length=4, min_length=4, label=_("OTP"))
    new_password = serializers.CharField(write_only=True, min_length=8, label=_("New Password"))
    confirm_password = serializers.CharField(write_only=True, min_length=8, label=_("Confirm Password"))

    def validate(self, data):
        if not data.get('email') or not data.get('otp') or not data.get('new_password') or not data.get('confirm_password'):
            raise serializers.ValidationError({"detail": _("All fields are required.")})

        if len(data['otp']) != 4 or not data['otp'].isdigit():
            raise serializers.ValidationError({"detail": _("Invalid OTP format.")})

        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"detail": _("Passwords do not match.")})

        return data

class OTPVerifySerializer(serializers.Serializer):
    code = serializers.CharField(max_length=4, min_length=4, label=_("OTP Code"))

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(_("OTP must contain only digits."))
        if len(value) != 4:
            raise serializers.ValidationError(_("OTP must be exactly 4 digits long."))
        return value

    def validate(self, attrs):
        code = attrs.get("code")
        user = self.context.get("user")

        try:
            otp = OTP.objects.filter(user=user, is_used=False).latest("created_at")
        except OTP.DoesNotExist:
            raise serializers.ValidationError(_("No valid OTP found."))

        if otp.code != code:
            raise serializers.ValidationError(_("Invalid OTP."))

        from django.utils import timezone
        import datetime
        if timezone.now() - otp.created_at > datetime.timedelta(minutes=5):
            raise serializers.ValidationError(_("OTP has expired."))

        otp.is_used = True
        otp.save()
        user.is_active = True
        user.save()

        attrs["otp"] = otp
        return attrs
    

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, label=_("Old Password"))
    new_password = serializers.CharField(write_only=True, label=_("New Password"))
    confirm_password = serializers.CharField(write_only=True, label=_("Confirm Password"))

    def validate(self, data):
        user = self.context['request'].user

        if not user.check_password(data['old_password']):
            raise serializers.ValidationError({"old_password": _("Old password is incorrect.")})

        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": _("New passwords do not match.")})

        if len(data['new_password']) < 6 or len(data['new_password']) > 16:
            raise serializers.ValidationError({"new_password": _("Password must be between 6 and 16 characters.")})

        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
    

User = get_user_model()
class NotificationSerializer(serializers.ModelSerializer):
    recipients = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'recipients', 'created_at', 'read']
        extra_kwargs = {
            'title': {'label': _("Title")},
            'message': {'label': _("Message")},
            'recipients': {'label': _("Recipients")},
            'created_at': {'label': _("Created At")},
            'read': {'label': _("Read")},
        }


class NotificationCreateSerializer(serializers.ModelSerializer):
    recipient_ids = serializers.ListField(
        child=serializers.IntegerField(label=_("Recipient ID")),
        write_only=True,
        required=False,
        allow_empty=True,
        label=_("Recipients")
    )

    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'recipient_ids', 'created_at']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'title': {'label': _("Title")},
            'message': {'label': _("Message")},
            'created_at': {'label': _("Created At")},
        }

    def create(self, validated_data):
        recipient_ids = validated_data.pop('recipient_ids', None)
        notification = Notification.objects.create(**validated_data)

        if recipient_ids is None or recipient_ids == []:
            users = User.objects.all()
        else:
            users = User.objects.filter(id__in=recipient_ids)

        notification.recipients.set(users)
        return notification
    
