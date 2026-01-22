"""
Schema Views

CRUD operations for data schemas and their fields.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Schema, SchemaField
from ..serializers import SchemaSerializer, SchemaListSerializer, SchemaFieldSerializer
from ..permissions import IsNeuractAdminForUnsafeMethods


class SchemaViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Schema CRUD operations.

    GET /schemas/ - List all schemas
    POST /schemas/ - Create a new schema
    GET /schemas/{id}/ - Retrieve a schema
    PUT /schemas/{id}/ - Update a schema
    DELETE /schemas/{id}/ - Delete a schema
    POST /schemas/import/ - Bulk import schemas
    GET /schemas/export/ - Export all schemas
    """
    queryset = Schema.objects.prefetch_related('fields').all()
    permission_classes = [IsNeuractAdminForUnsafeMethods]

    def get_serializer_class(self):
        if self.action == 'list':
            return SchemaListSerializer
        return SchemaSerializer

    @action(detail=False, methods=['post'], url_path='import')
    def import_schemas(self, request):
        """
        Bulk import schemas.

        POST /schemas/import/
        Body: { "schemas": [...] }
        """
        schemas_data = request.data.get('schemas', [])

        if not isinstance(schemas_data, list):
            return Response(
                {'error': 'schemas must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )

        created = []
        errors = []

        for schema_data in schemas_data:
            serializer = SchemaSerializer(data=schema_data)
            if serializer.is_valid():
                try:
                    schema = serializer.save()
                    created.append(schema.name)
                except Exception as e:
                    errors.append({'name': schema_data.get('name'), 'error': str(e)})
            else:
                errors.append({'name': schema_data.get('name'), 'error': serializer.errors})

        return Response({
            'created': created,
            'errors': errors,
            'total_created': len(created),
            'total_errors': len(errors)
        }, status=status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='export')
    def export_schemas(self, request):
        """
        Export all schemas.

        GET /schemas/export/
        """
        schemas = Schema.objects.prefetch_related('fields').all()
        serializer = SchemaSerializer(schemas, many=True)
        return Response({'schemas': serializer.data})

    @action(detail=True, methods=['post'], url_path='fields')
    def add_field(self, request, pk=None):
        """
        Add a field to a schema.

        POST /schemas/{id}/fields/
        """
        schema = self.get_object()
        serializer = SchemaFieldSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(schema=schema)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path='fields/(?P<field_key>[^/.]+)')
    def remove_field(self, request, pk=None, field_key=None):
        """
        Remove a field from a schema.

        DELETE /schemas/{id}/fields/{field_key}/
        """
        schema = self.get_object()
        try:
            field = schema.fields.get(key=field_key)
            field.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except SchemaField.DoesNotExist:
            return Response(
                {'error': f'Field {field_key} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
