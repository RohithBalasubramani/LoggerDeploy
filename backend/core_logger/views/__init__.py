# Views package

# PLC Logger views
from .health import HealthView
from .schemas import SchemaViewSet
from .devices import DeviceViewSet
from .storage import StorageTargetViewSet
from .tables import DeviceTableViewSet
from .mappings import FieldMappingViewSet
from .jobs import JobViewSet
from .gateways import GatewayViewSet

# Re-export existing auth views from parent module
from ..views_auth import (
    RegisterUserView,
    LoginView,
    AssignNeuractAdminClientRole,
    TestP,
)

__all__ = [
    # Auth views
    'RegisterUserView',
    'LoginView',
    'AssignNeuractAdminClientRole',
    'TestP',
    # PLC Logger views
    'HealthView',
    'SchemaViewSet',
    'DeviceViewSet',
    'StorageTargetViewSet',
    'DeviceTableViewSet',
    'FieldMappingViewSet',
    'JobViewSet',
    'GatewayViewSet',
]
