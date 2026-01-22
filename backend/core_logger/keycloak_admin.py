import requests
from django.conf import settings


class KeycloakAdminError(Exception):
    pass


def _kc_url(path: str) -> str:
    return f"{settings.KEYCLOAK_BASE_URL.rstrip('/')}{path}"


def get_service_account_token() -> str:
    """
    Get admin token using client_credentials grant for the service account client.
    """
    token_url = _kc_url(
        f"/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token"
    )
    data = {
        "grant_type": "client_credentials",
        "client_id": settings.KEYCLOAK_ADMIN_CLIENT_ID,
        "client_secret": settings.KEYCLOAK_ADMIN_CLIENT_SECRET,
    }
    r = requests.post(token_url, data=data, timeout=10)
    if r.status_code != 200:
        raise KeycloakAdminError(f"Failed to get admin token: {r.status_code} {r.text}")

    return r.json()["access_token"]


def create_user(token: str, username: str, email: str, first_name: str = "", last_name: str = "", enabled: bool = True) -> str:
    """
    Create a user in Keycloak. Returns Keycloak user_id (UUID).
    """
    url = _kc_url(f"/admin/realms/{settings.KEYCLOAK_REALM}/users")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    payload = {
        "username": username,
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
        "enabled": enabled,
        "emailVerified": False,
    }

    r = requests.post(url, json=payload, headers=headers, timeout=10)

    # Keycloak often returns 201 with Location header (sometimes 204)
    if r.status_code not in (201, 204):
        raise KeycloakAdminError(f"User create failed: {r.status_code} {r.text}")

    location = r.headers.get("Location", "")
    if not location:
        # fallback: query by username if Location not present
        user_id = get_user_id_by_username(token, username)
        if not user_id:
            raise KeycloakAdminError("User created but user_id not found (no Location header)")
        return user_id

    return location.rstrip("/").split("/")[-1]


def get_user_id_by_username(token: str, username: str) -> str | None:
    url = _kc_url(f"/admin/realms/{settings.KEYCLOAK_REALM}/users")
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers, params={"username": username, "exact": "true"}, timeout=10)
    if r.status_code != 200:
        return None
    users = r.json()
    if not users:
        return None
    return users[0].get("id")


def set_user_password(token: str, user_id: str, password: str, temporary: bool = False) -> None:
    url = _kc_url(f"/admin/realms/{settings.KEYCLOAK_REALM}/users/{user_id}/reset-password")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"type": "password", "value": password, "temporary": temporary}

    r = requests.put(url, json=payload, headers=headers, timeout=10)
    if r.status_code != 204:
        raise KeycloakAdminError(f"Set password failed: {r.status_code} {r.text}")
    

def get_client_uuid(token: str, client_id: str) -> str:
    url = _kc_url(f"/admin/realms/{settings.KEYCLOAK_REALM}/clients")
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers, params={"clientId": client_id}, timeout=10)
    if r.status_code != 200:
        raise KeycloakAdminError(f"Client lookup failed: {r.status_code} {r.text}")
    arr = r.json()
    if not arr:
        raise KeycloakAdminError(f"Client not found: {client_id}")
    return arr[0]["id"]


def get_client_role(token: str, client_uuid: str, role_name: str) -> dict:
    url = _kc_url(f"/admin/realms/{settings.KEYCLOAK_REALM}/clients/{client_uuid}/roles/{role_name}")
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers, timeout=10)
    if r.status_code == 404:
        raise KeycloakAdminError(f"Client role not found: {role_name}")
    if r.status_code != 200:
        raise KeycloakAdminError(f"Client role fetch failed: {r.status_code} {r.text}")
    return r.json()


def assign_client_role_to_user(token: str, user_id: str, client_uuid: str, role_repr: dict) -> None:
    url = _kc_url(
        f"/admin/realms/{settings.KEYCLOAK_REALM}/users/{user_id}/role-mappings/clients/{client_uuid}"
    )
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.post(url, json=[role_repr], headers=headers, timeout=10)
    if r.status_code != 204:
        raise KeycloakAdminError(f"Assign client role failed: {r.status_code} {r.text}")
