from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Existing auth views
from .views import RegisterUserView, LoginView, AssignNeuractAdminClientRole, TestP

# New PLC logger views
from .views import (
    HealthView,
    SchemaViewSet,
    DeviceViewSet,
    StorageTargetViewSet,
    DeviceTableViewSet,
    FieldMappingViewSet,
    JobViewSet,
    GatewayViewSet,
)
from .views.networking import (
    PingView, TcpTestView, ModbusTestView,
    OpcuaTestView, OpcuaBrowseView, NicsView
)

# Main router
router = DefaultRouter()
router.register(r'schemas', SchemaViewSet, basename='schema')
router.register(r'devices', DeviceViewSet, basename='device')
router.register(r'storage', StorageTargetViewSet, basename='storage')
router.register(r'tables', DeviceTableViewSet, basename='table')
router.register(r'jobs', JobViewSet, basename='job')
router.register(r'gateways', GatewayViewSet, basename='gateway')

# Mappings router (nested under tables manually)
mappings_router = DefaultRouter()
mappings_router.register(r'mappings', FieldMappingViewSet, basename='mapping')

urlpatterns = [
    # Keycloak authentication endpoints (existing)
    path("register/", RegisterUserView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("users/<str:username>/roles/client-neuract-admin/", AssignNeuractAdminClientRole.as_view()),
    path("test/", TestP.as_view()),

    # Health check (unauthenticated)
    path("health/", HealthView.as_view(), name="health"),

    # Networking diagnostics
    path("networking/ping/", PingView.as_view(), name="ping"),
    path("networking/tcp_test/", TcpTestView.as_view(), name="tcp-test"),
    path("networking/modbus/test/", ModbusTestView.as_view(), name="modbus-test"),
    path("networking/opcua/test/", OpcuaTestView.as_view(), name="opcua-test"),
    path("networking/opcua/browse/", OpcuaBrowseView.as_view(), name="opcua-browse"),
    path("networking/nics/", NicsView.as_view(), name="nics"),

    # Router URLs
    path("", include(router.urls)),

    # Nested mappings under tables: /tables/{table_pk}/mappings/
    path("tables/<uuid:table_pk>/", include(mappings_router.urls)),
]
