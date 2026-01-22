"""
Device Table Views

CRUD operations for device tables and schema migration.
"""

from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import DeviceTable, TableStatus, MappingHealth
from ..serializers import (
    DeviceTableSerializer, DeviceTableListSerializer, DeviceTableCreateSerializer
)
from ..permissions import IsNeuractAdminForUnsafeMethods
from ..services import StorageService


class DeviceTableViewSet(viewsets.ModelViewSet):
    """
    ViewSet for DeviceTable CRUD operations.

    GET /tables/ - List all device tables
    POST /tables/ - Create a new device table
    GET /tables/{id}/ - Retrieve a device table
    PUT /tables/{id}/ - Update a device table
    DELETE /tables/{id}/ - Delete a device table
    POST /tables/{id}/migrate/ - Create physical table in storage
    GET /tables/{id}/discover/ - Discover if table exists in storage
    POST /tables/{id}/bind_device/ - Bind a device to the table
    """
    queryset = DeviceTable.objects.select_related(
        'schema', 'storage_target', 'device'
    ).prefetch_related('mappings', 'schema__fields').all()
    permission_classes = [IsNeuractAdminForUnsafeMethods]

    def get_serializer_class(self):
        if self.action == 'list':
            return DeviceTableListSerializer
        if self.action == 'create':
            return DeviceTableCreateSerializer
        return DeviceTableSerializer

    def perform_create(self, serializer):
        """Create device table with default storage target if not specified."""
        storage_target = serializer.validated_data.get('storage_target')

        if not storage_target:
            from ..models import StorageTarget
            try:
                storage_target = StorageTarget.objects.get(is_default=True)
                serializer.save(storage_target=storage_target)
            except StorageTarget.DoesNotExist:
                serializer.save()
        else:
            serializer.save()

    @action(detail=True, methods=['post'])
    def migrate(self, request, pk=None):
        """
        Create the physical table in the storage target.

        POST /tables/{id}/migrate/
        """
        table = self.get_object()

        if not table.storage_target:
            return Response(
                {'error': 'No storage target configured for this table'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get column definitions from schema
        columns = []
        for field in table.schema.fields.all():
            columns.append({
                'key': field.key,
                'field_type': field.field_type
            })

        if not columns:
            return Response(
                {'error': 'Schema has no fields defined'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create the table
        success, error = StorageService().create_table(
            provider=table.storage_target.provider,
            connection_string=table.storage_target.connection_string,
            table_name=table.name,
            columns=columns
        )

        if success:
            table.status = TableStatus.MIGRATED
            table.last_migrated_at = timezone.now()
            table.last_error = ''
        else:
            table.status = TableStatus.ERROR
            table.last_error = error

        table.save(update_fields=['status', 'last_migrated_at', 'last_error', 'updated_at'])

        return Response({
            'ok': success,
            'table_id': str(table.id),
            'table_name': table.name,
            'status': table.status,
            'error': error
        })

    @action(detail=True, methods=['get'])
    def discover(self, request, pk=None):
        """
        Check if the physical table exists in the storage target.

        GET /tables/{id}/discover/
        """
        table = self.get_object()

        if not table.storage_target:
            return Response(
                {'error': 'No storage target configured for this table'},
                status=status.HTTP_400_BAD_REQUEST
            )

        exists = StorageService().table_exists(
            provider=table.storage_target.provider,
            connection_string=table.storage_target.connection_string,
            table_name=table.name
        )

        return Response({
            'table_id': str(table.id),
            'table_name': table.name,
            'exists': exists,
            'storage_target': table.storage_target.name
        })

    @action(detail=True, methods=['post'])
    def bind_device(self, request, pk=None):
        """
        Bind a device to this table.

        POST /tables/{id}/bind_device/
        Body: { "device_id": "..." }
        """
        table = self.get_object()
        device_id = request.data.get('device_id')

        if not device_id:
            return Response(
                {'error': 'device_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from ..models import Device
        try:
            device = Device.objects.get(id=device_id)
        except Device.DoesNotExist:
            return Response(
                {'error': f'Device {device_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        table.device = device
        table.save(update_fields=['device', 'updated_at'])

        return Response({
            'ok': True,
            'table_id': str(table.id),
            'device_id': str(device.id),
            'device_name': device.name
        })

    @action(detail=True, methods=['post'])
    def unbind_device(self, request, pk=None):
        """
        Unbind the device from this table.

        POST /tables/{id}/unbind_device/
        """
        table = self.get_object()
        table.device = None
        table.save(update_fields=['device', 'updated_at'])

        return Response({
            'ok': True,
            'table_id': str(table.id),
            'device_id': None
        })

    @action(detail=True, methods=['get'])
    def mapping_health(self, request, pk=None):
        """
        Get the mapping health status for this table.

        GET /tables/{id}/mapping_health/
        """
        table = self.get_object()
        schema_fields = set(table.schema.fields.values_list('key', flat=True))
        mapped_fields = set(table.mappings.values_list('field_key', flat=True))

        if not schema_fields:
            health = MappingHealth.UNMAPPED
        elif mapped_fields >= schema_fields:
            health = MappingHealth.MAPPED
        elif mapped_fields:
            health = MappingHealth.PARTIAL
        else:
            health = MappingHealth.UNMAPPED

        # Update table if health changed
        if table.mapping_health != health:
            table.mapping_health = health
            table.save(update_fields=['mapping_health', 'updated_at'])

        return Response({
            'table_id': str(table.id),
            'mapping_health': health,
            'schema_fields': list(schema_fields),
            'mapped_fields': list(mapped_fields),
            'unmapped_fields': list(schema_fields - mapped_fields)
        })
