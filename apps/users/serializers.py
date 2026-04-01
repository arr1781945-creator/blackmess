import secrets
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import (
    BankUser, UserProfile, UserRole, UserRoleAssignment,
    MFADevice, LoginSession, DeviceFingerprint, APIKey, UserPublicKey
)


class BankTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["employee_id"] = user.employee_id
        token["clearance"] = user.clearance_level
        token["mfa_verified"] = user.is_mfa_verified
        token["roles"] = list(
            user.role_assignments.filter(is_active=True).values_list("role__name", flat=True)
        )
        return token


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["title", "bio_encrypted", "timezone", "locale", "notification_prefs", "theme"]
        extra_kwargs = {"bio_encrypted": {"write_only": True}}


class BankUserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    roles = serializers.SerializerMethodField()

    class Meta:
        model = BankUser
        fields = [
            "id", "username", "email", "employee_id", "first_name", "last_name",
            "department", "clearance_level", "is_mfa_verified",
            "avatar_ipfs_cid", "last_active", "is_locked", "profile", "roles",
        ]
        read_only_fields = ["id", "employee_id", "clearance_level", "is_locked", "last_active"]

    def get_roles(self, obj):
        return list(obj.role_assignments.filter(is_active=True).values_list("role__name", flat=True))


class BankUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = BankUser
        fields = ["username", "email", "first_name", "last_name", "department", "password", "password_confirm"]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError('Passwords do not match.')
        return attrs

    def create(self, validated_data):
        # Auto-generate unique employee_id
        for _ in range(10):
            eid = secrets.token_hex(4)
            if not BankUser.objects.filter(employee_id=eid).exists():
                break
        validated_data['employee_id'] = eid
        return BankUser.objects.create_user(**validated_data)


class MFADeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MFADevice
        fields = ["id", "device_type", "name", "is_primary", "is_confirmed", "last_used", "created_at"]
        read_only_fields = ["id", "is_confirmed", "last_used", "created_at"]


class MFAVerifySerializer(serializers.Serializer):
    device_id = serializers.UUIDField()
    otp_code = serializers.CharField(min_length=6, max_length=8)


class LoginSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginSession
        fields = ["id", "ip_address", "user_agent", "country_code", "created_at", "last_seen", "is_revoked"]


class UserPublicKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPublicKey
        fields = ["id", "key_type", "public_key_b64", "fingerprint", "is_current", "created_at"]
        read_only_fields = ["fingerprint", "created_at"]


class APIKeyCreateSerializer(serializers.ModelSerializer):
    raw_key = serializers.CharField(read_only=True)

    class Meta:
        model = APIKey
        fields = ["id", "name", "scopes", "expires_at", "raw_key"]
        read_only_fields = ["id", "raw_key"]


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError('Passwords do not match.')
        return attrs


class UserRoleAssignmentSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.name", read_only=True)
    workspace_name = serializers.CharField(source="workspace.name", read_only=True)

    class Meta:
        model = UserRoleAssignment
        fields = ["id", "role", "role_name", "workspace", "workspace_name", "granted_at", "expires_at", "is_active"]
        read_only_fields = ["granted_at"]
