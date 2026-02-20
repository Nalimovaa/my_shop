from rest_framework.authentication import TokenAuthentication
from users.models import Session
from rest_framework.exceptions import AuthenticationFailed
import jwt
from django.conf import settings


class JWTTokenAuthentication(TokenAuthentication):
    """
    JWT authentication layer:
    - Extract token from Authorization header
    - Decode JWT
    - Validate session
    - Validate user.is_active
    - Attach request.user
    """

    keyword = "Bearer"

    def authenticate_credentials(self, key):
        # Checking the token in Swagger and in a custom session
        session = Session.objects.filter(token=key, is_active=True).select_related("user").first()
        if not session or not session.user.is_active:
            raise AuthenticationFailed("Invalid or inactive token")
        return (session.user, session.token)

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return None  # DRF will treat as anonymous

        token = auth_header.split(" ")[1]

        try:
            jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid token")

        session = Session.objects.filter(
            token=token,
            is_active=True
        ).select_related("user").first()

        if not session or not session.user.is_active:
            raise AuthenticationFailed("Inactive session")

        return (session.user, token)
