from rest_framework import serializers
from django.contrib.auth import get_user_model
from core.models import AccessRolesRules
from users.models import Role, UserRole


User = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name']


class UserRoleSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all())

    class Meta:
        model = UserRole
        fields = ['id', 'user', 'role']


class AccessRulesSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    element = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = AccessRolesRules
        fields = [
            'id', 'role', 'element',
            'read_permission', 'read_all_permission',
            'create_permission', 'update_permission', 'update_all_permission',
            'delete_permission', 'delete_all_permission'
        ]

