import jwt
from rest_framework import viewsets, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.decorators import action
from users.models import Session
from django.contrib.auth import get_user_model
from users.serializers import UserSerializer, LoginSerializer
from users.permissions import IsCustomAuthenticated, RolePermission
from drf_spectacular.utils import extend_schema, OpenApiExample
from django.utils import timezone
from django.conf import settings
from rest_framework.request import Request
from rest_framework import serializers
from django.utils.timezone import now


User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsCustomAuthenticated, RolePermission]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:  # The admin sees everyone
            return User.objects.all()
        return User.objects.filter(id=user.id)  # a regular user only sees themselves

    def get_object(self):
        obj = super().get_object()
        if not self.request.user.is_superuser and obj != self.request.user:
            raise PermissionDenied("You do not have permission to access this user")
        return obj

    @extend_schema(
        summary="Register new user",
        description="Public endpoint for creating a new user account. "
                    "Requires email, password, password_repeat, first_name, last_name (optional), middle_name (optional). "
                    "The password will be hashed with bcrypt before saving.",
        request=UserSerializer,
        responses={
            201: OpenApiExample(
                'Example Response',
                value={
                    "id": 1,
                    "email": "user@example.com",
                    "fullname": "John Doe"
                },
                response_only=True,
                summary="Successfully created user"
            ),
            400: OpenApiExample(
                'Example Error',
                value={
                    "password_repeat": ["Пароли не совпадают"]
                },
                response_only=True,
                summary="Validation error"
            )
        }
    )
    @action(detail=False, methods=["post"], permission_classes=[])
    def register(self, request: Request):
        """Public endpoint for registration"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "id": user.id,
            "email": user.email,
            "fullname": user.fullname
        }, status=status.HTTP_201_CREATED)

    def get_client_ip(self, request: Request) -> str:
        """Gets the client's IP address from the X-Forwarded-For header or REMOTE_ADDR."""
        x_forwarded_for = request.headers.get('X-Forwarded-For')
        if x_forwarded_for:
            # X-Forwarded-For may contain several IP addresses; we take the first (original) one.
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            # Use REMOTE_ADDR if X-Forwarded-For is missing
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @extend_schema(
        summary="Login user",
        description=(
                "Public endpoint for logging in a user. "
                "Requires email and password. Returns JWT token and user info. "
                "Token is valid until logout. "
                "Frontend should store token and use it in Authorization header for subsequent requests."
        ),
        request=LoginSerializer,
        responses={
            200: OpenApiExample(
                'Example Response',
                value={
                    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "user_id": 1,
                    "email": "user@example.com"
                },
                response_only=True,
                summary="Successfully logged in"
            ),
            400: OpenApiExample(
                'Example Error',
                value={"detail": "Email and password required"},
                response_only=True,
                summary="Validation error"
            ),
            401: OpenApiExample(
                'Example Error',
                value={"detail": "Invalid credentials"},
                response_only=True,
                summary="Invalid email or password"
            ),
            403: OpenApiExample(
                'Example Error',
                value={"detail": "User is deactivated"},
                response_only=True,
                summary="User soft-deleted / deactivated"
            ),
        }
    )
    @action(detail=False, methods=["post"], permission_classes=[])
    def login(self, request):
        """
        Email + password verification
        JWT generation
        Session creation
        Token return
        """

        serializer = LoginSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            detail = e.detail.get("detail", "")
            if detail == "User is deactivated":
                return Response({"detail": detail}, status=status.HTTP_403_FORBIDDEN)
            return Response({"detail": detail}, status=status.HTTP_401_UNAUTHORIZED)

        user = serializer.validated_data["user"]

        # Generating JWT
        payload = {
            "user_id": user.id,
            "iat": timezone.now()
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        # Creating a Session
        Session.objects.create(
            user=user,
            token=token,
            is_active=True,
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            ip_address=self.get_client_ip(request)
        )

        return Response({
            "token": token,
            "user_id": user.id,
            "email": user.email
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Logout user",
        description="Endpoint for logging out the current user. "
                    "Deactivates the JWT session so the token cannot be used anymore.",
        request=None,
        responses={
            200: OpenApiExample(
                'Example Response',
                value={"detail": "Successfully logged out"},
                response_only=True,
                summary="Logout success"
            ),
            401: OpenApiExample(
                'Example Error',
                value={"detail": "Authorization header missing or invalid"},
                response_only=True,
                summary="Unauthorized"
            )
        }
    )
    @action(detail=False, methods=["post"], permission_classes=[IsCustomAuthenticated])
    def logout(self, request):
        """Deactivate the current user's session based on the JWT token"""
        token = request.headers.get("Authorization").split(" ")[1].strip()
        Session.objects.filter(token=token, is_active=True).update(is_active=False)
        return Response({"detail": "Successfully logged out"}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Soft delete user",
        description=(
                "Endpoint for soft-deleting the current user. "
                "Marks `user.is_active = False` and deactivates all active sessions."
        ),
        request=None,
        responses={
            200: OpenApiExample(
                'Example Response',
                value={"detail": "User soft-deleted"},
                response_only=True,
                summary="User soft-deleted"
            ),
            401: OpenApiExample(
                'Example Error',
                value={"detail": "Authorization header missing or invalid"},
                response_only=True,
                summary="Unauthorized"
            )
        }
    )
    @action(detail=False, methods=["post"], permission_classes=[IsCustomAuthenticated])
    def delete(self, request):
        """Soft delete the current user"""
        user = request.user

        # soft delete user
        user.is_active = False
        user.save()

        # deactivation of all sessions and setting an expiration date
        Session.objects.filter(user=user, is_active=True).update(
            is_active=False,
            expires_at=now()
        )

        return Response({"detail": "User soft-deleted"}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update user profile",
        description=(
                "Endpoint for updating the current user's profile. "
                "User can modify their personal information: email, first_name, last_name, middle_name, password. "
                "Requires authentication. Returns 401 if user is not logged in, 403 if forbidden."
        ),
        request=UserSerializer,
        responses={
            200: OpenApiExample(
                'Example Response',
                value={
                    "id": 9,
                    "email": "new_email@example.com",
                    "first_name": "Alice",
                    "last_name": "Colman",
                    "middle_name": "J",
                },
                response_only=True,
                summary="Profile updated successfully"
            ),
            401: OpenApiExample(
                'Example Error',
                value={"detail": "Authorization header missing or invalid"},
                response_only=True,
                summary="Unauthorized"
            ),
            403: OpenApiExample(
                'Example Error',
                value={"detail": "You do not have permission to access this user"},
                response_only=True,
                summary="Forbidden"
            )
        }
    )
    @action(detail=False, methods=["put", "patch"], permission_classes=[IsCustomAuthenticated, RolePermission])
    def update_profile(self, request):
        """Update current user's profile"""
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

