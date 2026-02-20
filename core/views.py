from drf_spectacular.utils import OpenApiParameter, extend_schema, OpenApiExample
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from users.models import UserRole
from .models import AccessRolesRules, BusinessElement
from .serializers import UserRoleSerializer, AccessRulesSerializer
from users.permissions import IsCustomAuthenticated, RolePermission
from django.contrib.auth import get_user_model
from drf_spectacular.types import OpenApiTypes


User = get_user_model()


class AdminRolesViewSet(viewsets.ViewSet):
    """API for managing user roles and rules"""
    permission_classes = [IsCustomAuthenticated, RolePermission]
    business_element = "UserRole"

    @extend_schema(
        summary="Список ролей пользователя",
        description="Возвращает роли конкретного пользователя по `user_id`",
        parameters=[
            OpenApiParameter(
                name="user_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="ID пользователя, для которого нужно получить роли",
                required=True,
            )
        ],
        responses={
            200: UserRoleSerializer,
            400: OpenApiExample(
                "Bad Request",
                value={"detail": "user_id query param is required"}
            ),
            401: OpenApiExample(
                "Unauthorized",
                value={"detail": "User not authenticated"}
            ),
            403: OpenApiExample(
                "Forbidden",
                value={"detail": "You do not have permission to access UserRole"}
            ),
        }
    )
    @action(detail=False, methods=["get"])
    def list_user_roles(self, request):
        """List of roles for a specific user"""
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response(
                {"detail": "user_id query param is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем, существует ли пользователь
        try:
            User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        user_roles = UserRole.objects.filter(user_id=user_id).select_related("role")
        serializer = UserRoleSerializer(user_roles, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Назначить роль пользователю",
        description="Добавляет указанную роль пользователю",
        request=UserRoleSerializer,
        responses={
            201: UserRoleSerializer,
            400: OpenApiExample("Bad Request", value={"detail": "Invalid data"}),
            401: OpenApiExample("Unauthorized", value={"detail": "User not authenticated"}),
            403: OpenApiExample("Forbidden", value={"detail": "You do not have permission to assign role"}),
        }
    )
    @action(detail=False, methods=["post"])
    def assign_role(self, request):
        """Assign a role to a user"""
        user_id = request.data.get("user")
        role_id = request.data.get("role")

        if not user_id or not role_id:
            return Response(
                {"detail": "Both 'user' and 'role' are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check whether such an entry already exists.
        exists = UserRole.objects.filter(user_id=user_id, role_id=role_id).exists()
        if exists:
            return Response(
                {"detail": "This role is already assigned to the user"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Creating a new connection
        serializer = UserRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Удалить роль у пользователя",
        description="Удаляет роль у пользователя",
        request=UserRoleSerializer,
        responses={
            200: OpenApiExample("Role removed", value={"detail": "Role removed"}),
            400: OpenApiExample("Bad Request", value={"detail": "user and role are required"}),
            401: OpenApiExample("Unauthorized", value={"detail": "User not authenticated"}),
            403: OpenApiExample("Forbidden", value={"detail": "You do not have permission to remove role"}),
            404: OpenApiExample("Not Found", value={"detail": "Role not found for user"}),
        }
    )
    @action(detail=False, methods=["post"])
    def remove_role(self, request):
        """Revoke a user's role"""
        user_id = request.data.get("user")
        role_id = request.data.get("role")
        if not user_id or not role_id:
            return Response({"detail": "user and role are required"}, status=status.HTTP_400_BAD_REQUEST)

        deleted_count, _ = UserRole.objects.filter(user_id=user_id, role_id=role_id).delete()
        if deleted_count == 0:
            return Response({"detail": "Role not found for user"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"detail": "Role removed"}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Список всех правил доступа",
        description="Возвращает все правила доступа для всех ролей и элементов",
        responses={
            200: AccessRulesSerializer,
            401: OpenApiExample("Unauthorized", value={"detail": "User not authenticated"}),
            403: OpenApiExample("Forbidden", value={"detail": "You do not have permission to view access rules"}),
        }
    )
    @action(detail=False, methods=["get"])
    def access_rules(self, request):
        """List of all access rules"""
        rules = AccessRolesRules.objects.select_related('role', 'element')
        serializer = AccessRulesSerializer(rules, many=True)
        return Response(serializer.data)


class RBACListModelViewSet(viewsets.ModelViewSet):
    """Only override get_queryset to control
    which objects the user can see in list()"""

    def get_queryset(self):
        user = self.request.user

        # If the user is a superuser, we grant full access to all objects without restrictions
        if user.is_superuser:
            return super().get_queryset()

        # Get the name of the business element from ViewSet
        element_name = getattr(self, "business_element", None)

        # Search for the corresponding BusinessElement object in the database
        element = BusinessElement.objects.filter(name=element_name).first()

        # Get all roles of the current user
        user_roles = user.user_roles.select_related("role")

        # We receive all user access rules
        rules = AccessRolesRules.objects.filter(
            role__in=[ur.role for ur in user_roles],  # список ролей пользователя
            element=element  # текущий бизнес-элемент
        )

        # If a user has at least one rule where read_all_permission = True, they can see ALL objects.
        if any(rule.read_all_permission for rule in rules):
            return super().get_queryset()

        # If read_permission = True, the user can only see their own objects.
        if any(rule.read_permission for rule in rules):
            return super().get_queryset().filter(owner=user)

        # If there is neither read_all_permission nor read_permission, return an empty queryset.
        return super().get_queryset().none()
