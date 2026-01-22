"""
Field Mapping Views

CRUD operations for field-to-address mappings.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import DeviceTable, FieldMapping, MappingHealth
from ..serializers import FieldMappingSerializer, FieldMappingBulkSerializer
from ..permissions import IsNeuractAdminForUnsafeMethods
from ..services import ModbusService, OpcuaService


class FieldMappingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for FieldMapping CRUD operations.

    All endpoints are scoped to a device table via URL parameter.

    GET /tables/{table_id}/mappings/ - List mappings for a table
    POST /tables/{table_id}/mappings/ - Create a mapping
    GET /tables/{table_id}/mappings/{id}/ - Retrieve a mapping
    PUT /tables/{table_id}/mappings/{id}/ - Update a mapping
    DELETE /tables/{table_id}/mappings/{id}/ - Delete a mapping
    POST /tables/{table_id}/mappings/bulk/ - Bulk upsert mappings
    POST /tables/{table_id}/mappings/validate/ - Validate mappings
    GET /tables/{table_id}/mappings/export/ - Export mappings
    POST /tables/{table_id}/mappings/import/ - Import mappings
    """
    serializer_class = FieldMappingSerializer
    permission_classes = [IsNeuractAdminForUnsafeMethods]

    def get_queryset(self):
        table_id = self.kwargs.get('table_pk')
        return FieldMapping.objects.filter(device_table_id=table_id)

    def get_table(self):
        table_id = self.kwargs.get('table_pk')
        return DeviceTable.objects.select_related(
            'schema', 'device', 'device__modbus_config', 'device__opcua_config'
        ).get(id=table_id)

    def perform_create(self, serializer):
        table = self.get_table()
        serializer.save(device_table=table)
        self._update_mapping_health(table)

    def perform_update(self, serializer):
        serializer.save()
        self._update_mapping_health(self.get_table())

    def perform_destroy(self, instance):
        table = instance.device_table
        instance.delete()
        self._update_mapping_health(table)

    @action(detail=False, methods=['post'])
    def bulk(self, request, table_pk=None):
        """
        Bulk upsert mappings for a table.

        POST /tables/{table_id}/mappings/bulk/
        Body: { "mappings": [...] }
        """
        table = self.get_table()
        mappings_data = request.data.get('mappings', [])

        if not isinstance(mappings_data, list):
            return Response(
                {'error': 'mappings must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )

        created = 0
        updated = 0
        errors = []

        for mapping_data in mappings_data:
            field_key = mapping_data.get('field_key')
            if not field_key:
                errors.append({'error': 'field_key is required', 'data': mapping_data})
                continue

            try:
                existing = FieldMapping.objects.filter(
                    device_table=table,
                    field_key=field_key
                ).first()

                if existing:
                    serializer = FieldMappingSerializer(existing, data=mapping_data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        updated += 1
                    else:
                        errors.append({'field_key': field_key, 'error': serializer.errors})
                else:
                    serializer = FieldMappingSerializer(data=mapping_data)
                    if serializer.is_valid():
                        serializer.save(device_table=table)
                        created += 1
                    else:
                        errors.append({'field_key': field_key, 'error': serializer.errors})

            except Exception as e:
                errors.append({'field_key': field_key, 'error': str(e)})

        self._update_mapping_health(table)

        return Response({
            'created': created,
            'updated': updated,
            'errors': errors,
            'total_processed': created + updated,
            'total_errors': len(errors)
        })

    @action(detail=False, methods=['post'])
    def validate(self, request, table_pk=None):
        """
        Validate mappings by attempting to read values.

        POST /tables/{table_id}/mappings/validate/
        """
        table = self.get_table()

        if not table.device:
            return Response(
                {'error': 'No device bound to this table'},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = []
        mappings = table.mappings.all()

        for mapping in mappings:
            result = {
                'field_key': mapping.field_key,
                'address': mapping.address,
                'protocol': mapping.protocol,
                'ok': False,
                'value': None,
                'error': None
            }

            try:
                value = self._read_mapping_value(table.device, mapping)
                result['ok'] = True
                result['value'] = value
            except Exception as e:
                result['error'] = str(e)

            results.append(result)

        ok_count = sum(1 for r in results if r['ok'])
        return Response({
            'table_id': str(table.id),
            'device_id': str(table.device.id),
            'total': len(results),
            'ok': ok_count,
            'failed': len(results) - ok_count,
            'results': results
        })

    @action(detail=False, methods=['get'], url_path='export')
    def export_mappings(self, request, table_pk=None):
        """
        Export mappings for a table.

        GET /tables/{table_id}/mappings/export/
        """
        table = self.get_table()
        mappings = table.mappings.all()
        serializer = FieldMappingSerializer(mappings, many=True)

        return Response({
            'table_id': str(table.id),
            'table_name': table.name,
            'mappings': serializer.data
        })

    @action(detail=False, methods=['post'], url_path='import')
    def import_mappings(self, request, table_pk=None):
        """
        Import mappings for a table (replaces existing).

        POST /tables/{table_id}/mappings/import/
        Body: { "mappings": [...] }
        """
        table = self.get_table()
        mappings_data = request.data.get('mappings', [])

        if not isinstance(mappings_data, list):
            return Response(
                {'error': 'mappings must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Delete existing mappings
        table.mappings.all().delete()

        # Create new mappings
        created = 0
        errors = []

        for mapping_data in mappings_data:
            serializer = FieldMappingSerializer(data=mapping_data)
            if serializer.is_valid():
                serializer.save(device_table=table)
                created += 1
            else:
                errors.append({
                    'field_key': mapping_data.get('field_key'),
                    'error': serializer.errors
                })

        self._update_mapping_health(table)

        return Response({
            'created': created,
            'errors': errors
        })

    @action(detail=False, methods=['post'], url_path='copy_from/(?P<source_table_pk>[^/.]+)')
    def copy_from(self, request, table_pk=None, source_table_pk=None):
        """
        Copy mappings from another table.

        POST /tables/{table_id}/mappings/copy_from/{source_table_id}/
        """
        target_table = self.get_table()

        try:
            source_table = DeviceTable.objects.get(id=source_table_pk)
        except DeviceTable.DoesNotExist:
            return Response(
                {'error': f'Source table {source_table_pk} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Copy mappings
        created = 0
        for source_mapping in source_table.mappings.all():
            FieldMapping.objects.update_or_create(
                device_table=target_table,
                field_key=source_mapping.field_key,
                defaults={
                    'protocol': source_mapping.protocol,
                    'address': source_mapping.address,
                    'data_type': source_mapping.data_type,
                    'scale': source_mapping.scale,
                    'deadband': source_mapping.deadband,
                    'byte_order': source_mapping.byte_order,
                    'poll_interval_ms': source_mapping.poll_interval_ms,
                }
            )
            created += 1

        self._update_mapping_health(target_table)

        return Response({
            'source_table': source_table.name,
            'target_table': target_table.name,
            'mappings_copied': created
        })

    def _read_mapping_value(self, device, mapping):
        """Read a single mapping value from the device."""
        if mapping.protocol == 'modbus':
            if not hasattr(device, 'modbus_config'):
                raise ValueError('Device has no Modbus configuration')

            config = device.modbus_config
            return ModbusService().read_value(
                host=config.host,
                port=config.port,
                address=int(mapping.address),
                data_type=mapping.data_type,
                unit_id=config.unit_id,
                byte_order=mapping.byte_order,
                scale=mapping.scale
            )

        elif mapping.protocol == 'opcua':
            if not hasattr(device, 'opcua_config'):
                raise ValueError('Device has no OPC UA configuration')

            config = device.opcua_config
            return OpcuaService().read_value(
                endpoint=config.endpoint,
                node_id=mapping.address,
                auth_type=config.auth_type,
                username=config.username,
                password=config.password,
                scale=mapping.scale
            )

        else:
            raise ValueError(f'Unknown protocol: {mapping.protocol}')

    def _update_mapping_health(self, table):
        """Update the mapping health status for a table."""
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

        if table.mapping_health != health:
            table.mapping_health = health
            table.save(update_fields=['mapping_health', 'updated_at'])
