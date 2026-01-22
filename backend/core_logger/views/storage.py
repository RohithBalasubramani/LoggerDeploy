"""
Storage Target Views

CRUD operations for database storage targets.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import StorageTarget
from ..serializers import StorageTargetSerializer, StorageTargetTestSerializer
from ..permissions import IsNeuractAdminForUnsafeMethods
from ..services import StorageService


class StorageTargetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for StorageTarget CRUD operations.

    GET /storage/ - List all storage targets
    POST /storage/ - Create a new storage target
    GET /storage/{id}/ - Retrieve a storage target
    PUT /storage/{id}/ - Update a storage target
    DELETE /storage/{id}/ - Delete a storage target
    POST /storage/test/ - Test connection (without saving)
    POST /storage/{id}/test/ - Test existing target connection
    POST /storage/{id}/set_default/ - Set as default target
    """
    queryset = StorageTarget.objects.all()
    serializer_class = StorageTargetSerializer
    permission_classes = [IsNeuractAdminForUnsafeMethods]

    def perform_create(self, serializer):
        """Create target and test connection."""
        target = serializer.save()
        self._test_and_update_target(target)

    def destroy(self, request, *args, **kwargs):
        """Prevent deletion of default or in-use targets."""
        target = self.get_object()

        if target.is_default:
            return Response(
                {'error': 'Cannot delete the default storage target'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if target is in use by any device tables
        if target.device_tables.exists():
            return Response(
                {'error': 'Cannot delete storage target that is in use by device tables'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def test(self, request):
        """
        Test a storage target connection without saving.

        POST /storage/test/
        Body: { "provider": "postgres", "connection_string": "..." }
        """
        serializer = StorageTargetTestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        provider = serializer.validated_data['provider']
        connection_string = serializer.validated_data['connection_string']

        success, latency, error = StorageService().test_connection(
            provider=provider,
            connection_string=connection_string
        )

        return Response({
            'ok': success,
            'provider': provider,
            'latency_ms': latency,
            'error': error
        })

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """
        Test an existing storage target connection.

        POST /storage/{id}/test/
        """
        target = self.get_object()
        success, latency, error = self._test_and_update_target(target)

        return Response({
            'ok': success,
            'target_id': str(target.id),
            'target_name': target.name,
            'status': target.status,
            'latency_ms': latency,
            'error': error
        })

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """
        Set a storage target as the default.

        POST /storage/{id}/set_default/
        """
        target = self.get_object()
        target.is_default = True
        target.save()  # save() method handles clearing other defaults

        return Response({
            'ok': True,
            'target_id': str(target.id),
            'target_name': target.name,
            'is_default': True
        })

    @action(detail=False, methods=['get'])
    def default(self, request):
        """
        Get the default storage target.

        GET /storage/default/
        """
        try:
            target = StorageTarget.objects.get(is_default=True)
            serializer = self.get_serializer(target)
            return Response(serializer.data)
        except StorageTarget.DoesNotExist:
            return Response(
                {'error': 'No default storage target configured'},
                status=status.HTTP_404_NOT_FOUND
            )

    def _test_and_update_target(self, target):
        """
        Test connection and update target status.

        Returns:
            Tuple of (success, latency_ms, error_message)
        """
        success, latency, error = StorageService().test_connection(
            provider=target.provider,
            connection_string=target.connection_string
        )

        if success:
            target.status = 'connected'
            target.last_error = ''
        else:
            target.status = 'error'
            target.last_error = error

        target.save(update_fields=['status', 'last_error', 'updated_at'])
        return success, latency, error
