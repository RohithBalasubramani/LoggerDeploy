from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from .keycloak_admin import *
from django.conf import settings
from .permissions import IsNeuractAdminForUnsafeMethods

from .keycloak_admin import (
    KeycloakAdminError,
    get_service_account_token,
    create_user,
    set_user_password,
)

class RegisterUserView(APIView):
    """
    POST /auth/register/
    Body:
      {
        "username": "rohith",
        "email": "rohith@example.com",
        "password": "secret123",
        "first_name": "Rohith",
        "last_name": "K",
        "enabled": true
      }
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = request.data.get("username", "").strip()
        email = request.data.get("email", "").strip()
        password = request.data.get("password", "")
        first_name = request.data.get("first_name", "").strip()
        last_name = request.data.get("last_name", "").strip()
        enabled = bool(request.data.get("enabled", True))

        if not username or not email or not password:
            return Response(
                {"detail": "username, email, password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = get_service_account_token()
            user_id = create_user(
                token=token,
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                enabled=enabled,
            )
            set_user_password(token=token, user_id=user_id, password=password, temporary=False)

            return Response(
                {"ok": True, "user_id": user_id, "username": username, "email": email},
                status=status.HTTP_201_CREATED,
            )

        except KeycloakAdminError as e:
            return Response(
                {"detail": "Keycloak error", "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"detail": "Server error", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        password = request.data.get("password") or ""

        if not username or not password:
            return Response({"detail": "username and password are required"}, status=400)

        # ✅ Correct Keycloak token endpoint (NO "/protocol" here)
        token_url = (
            f"{settings.KEYCLOAK_BASE_URL.rstrip('/')}/realms/{settings.KEYCLOAK_REALM}"
            f"/protocol/openid-connect/token"
        )

        data = {
            "grant_type": "password",
            "client_id": settings.KEYCLOAK_ADMIN_CLIENT_ID,   # ok if using same client
            "username": username,
            "password": password,
        }

        secret = getattr(settings, "KEYCLOAK_ADMIN_CLIENT_SECRET", "")
        if secret:
            data["client_secret"] = secret

        r = requests.post(token_url, data=data, timeout=10)

        try:
            payload = r.json()
        except ValueError:
            payload = {"raw": r.text}

        if r.status_code != 200:
            return Response({"detail": "Login failed", "keycloak": payload}, status=401)

        return Response(payload, status=200)



class AssignNeuractAdminClientRole(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, username: str):
        try:
            token = get_service_account_token()

            user_id = get_user_id_by_username(token, username)
            if not user_id:
                return Response({"ok": False, "error": "User not found"}, status=404)

            client_uuid = get_client_uuid(token, settings.KEYCLOAK_ADMIN_CLIENT_ID)
            role = get_client_role(token, client_uuid, "neuract-admin")

            assign_client_role_to_user(token, user_id, client_uuid, role)

            return Response(
                {"ok": True, "username": username, "user_id": user_id, "client": settings.KEYCLOAK_ADMIN_CLIENT_ID, "role": "neuract-admin"},
                status=200,
            )

        except KeycloakAdminError as e:
            return Response({"ok": False, "error": str(e)}, status=400)
        


class TestP(APIView):
    permission_classes = [IsNeuractAdminForUnsafeMethods]

    def post(self, request):
        return Response({"worked": "done"})