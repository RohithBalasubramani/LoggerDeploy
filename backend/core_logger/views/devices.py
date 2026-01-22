"""
Device Views

CRUD operations for PLC devices and connection testing.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Device, DeviceStatus
from ..serializers import DeviceSerializer, DeviceListSerializer
from ..permissions import IsNeuractAdminForUnsafeMethods
from ..services import ModbusService, OpcuaService


class DeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Device CRUD operations.

    GET /devices/ - List all devices
    POST /devices/ - Create a new device
    GET /devices/{id}/ - Retrieve a device
    PUT /devices/{id}/ - Update a device
    DELETE /devices/{id}/ - Delete a device
    POST /devices/{id}/connect/ - Test connection
    POST /devices/{id}/disconnect/ - Mark as disconnected
    POST /devices/{id}/quick_test/ - Quick connection test
    """
    queryset = Device.objects.select_related('modbus_config', 'opcua_config').all()
    permission_classes = [IsNeuractAdminForUnsafeMethods]

    def get_serializer_class(self):
        if self.action == 'list':
            return DeviceListSerializer
        return DeviceSerializer

    def perform_create(self, serializer):
        """Create device and optionally test connection."""
        device = serializer.save()

        # Auto-test connection on create
        if self.request.data.get('test_connection', True):
            self._test_and_update_device(device)

    @action(detail=True, methods=['post'])
    def connect(self, request, pk=None):
        """
        Test connection to a device.

        POST /devices/{id}/connect/
        """
        device = self.get_object()
        success, latency, error = self._test_and_update_device(device)

        return Response({
            'ok': success,
            'device_id': str(device.id),
            'device_name': device.name,
            'status': device.status,
            'latency_ms': latency,
            'error': error
        })

    @action(detail=True, methods=['post'])
    def disconnect(self, request, pk=None):
        """
        Mark device as disconnected.

        POST /devices/{id}/disconnect/
        """
        device = self.get_object()

        # Disconnect from services
        if device.protocol == 'modbus' and hasattr(device, 'modbus_config'):
            config = device.modbus_config
            ModbusService().disconnect(config.host, config.port)
        elif device.protocol == 'opcua' and hasattr(device, 'opcua_config'):
            config = device.opcua_config
            OpcuaService().disconnect(config.endpoint)

        device.status = DeviceStatus.DISCONNECTED
        device.save(update_fields=['status', 'updated_at'])

        return Response({
            'ok': True,
            'device_id': str(device.id),
            'status': device.status
        })

    @action(detail=True, methods=['post'])
    def quick_test(self, request, pk=None):
        """
        Quick connection test without updating device status.

        POST /devices/{id}/quick_test/
        """
        device = self.get_object()
        success, latency, error = self._test_connection(device)

        return Response({
            'ok': success,
            'latency_ms': latency,
            'error': error
        })

    def _test_connection(self, device):
        """
        Test connection to a device.

        Returns:
            Tuple of (success, latency_ms, error_message)
        """
        try:
            if device.protocol == 'modbus':
                if not hasattr(device, 'modbus_config'):
                    return False, 0, 'No Modbus configuration'

                config = device.modbus_config
                return ModbusService().test_connection(
                    host=config.host,
                    port=config.port,
                    unit_id=config.unit_id,
                    timeout_ms=config.timeout_ms
                )

            elif device.protocol == 'opcua':
                if not hasattr(device, 'opcua_config'):
                    return False, 0, 'No OPC UA configuration'

                config = device.opcua_config
                success, latency, error, _ = OpcuaService().test_connection(
                    endpoint=config.endpoint,
                    auth_type=config.auth_type,
                    username=config.username,
                    password=config.password
                )
                return success, latency, error

            else:
                return False, 0, f'Unknown protocol: {device.protocol}'

        except Exception as e:
            return False, 0, str(e)

    def _test_and_update_device(self, device):
        """
        Test connection and update device status.

        Returns:
            Tuple of (success, latency_ms, error_message)
        """
        success, latency, error = self._test_connection(device)

        if success:
            device.status = DeviceStatus.CONNECTED
            device.latency_ms = latency
            device.last_error = ''
        else:
            device.status = DeviceStatus.ERROR
            device.latency_ms = None
            device.last_error = error

        device.save(update_fields=['status', 'latency_ms', 'last_error', 'updated_at'])
        return success, latency, error
