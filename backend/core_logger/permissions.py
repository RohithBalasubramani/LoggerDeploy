from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.conf import settings


class IsNeuractAdminForUnsafeMethods(BasePermission):
    """
    - SAFE methods: allow if token is present (authenticated via your Keycloak auth layer)
    - UNSAFE methods: require client role 'neuract-admin'
      extracted from: resource_access[KEYCLOAK_ROLE_CLIENT_ID].roles
    """

    required_role = "neuract-admin"

    def has_permission(self, request, view) -> bool:
        # Must have token claims available
        claims = getattr(request, "auth", None) or {}
        if not claims:
            return False

        # SAFE methods allowed for any authenticated user
        if request.method in SAFE_METHODS:
            return True

        # Which client’s roles to check
        client_id = getattr(settings, "KEYCLOAK_ROLE_CLIENT_ID", "neuract-logger")

        roles = (
            claims.get("resource_access", {})
                  .get(client_id, {})
                  .get("roles", [])
        )

        return self.required_role in roles
