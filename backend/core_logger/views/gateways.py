"""
Gateway Views

CRUD operations for network gateways.
"""

import socket
import subprocess
import platform
import time
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Gateway
from ..serializers import GatewaySerializer
from ..permissions import IsNeuractAdminForUnsafeMethods


class GatewayViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Gateway CRUD operations.

    GET /gateways/ - List all gateways
    POST /gateways/ - Create a new gateway
    GET /gateways/{id}/ - Retrieve a gateway
    PUT /gateways/{id}/ - Update a gateway
    DELETE /gateways/{id}/ - Delete a gateway
    POST /gateways/{id}/test/ - Test gateway reachability
    POST /gateways/{id}/test_ports/ - Test TCP ports on gateway
    """
    queryset = Gateway.objects.all()
    serializer_class = GatewaySerializer
    permission_classes = [IsNeuractAdminForUnsafeMethods]

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """
        Test gateway reachability via ping.

        POST /gateways/{id}/test/
        """
        gateway = self.get_object()
        timeout_ms = request.data.get('timeout_ms', 3000)

        success, latency, error = self._ping_host(gateway.host, timeout_ms)

        # Update gateway status
        if success:
            gateway.status = 'reachable'
            gateway.last_ping_ms = latency
        else:
            gateway.status = 'unreachable'
            gateway.last_ping_ms = None

        gateway.save(update_fields=['status', 'last_ping_ms', 'updated_at'])

        return Response({
            'ok': success,
            'gateway_id': str(gateway.id),
            'gateway_name': gateway.name,
            'host': gateway.host,
            'latency_ms': latency,
            'error': error
        })

    @action(detail=True, methods=['post'])
    def test_ports(self, request, pk=None):
        """
        Test TCP ports on the gateway.

        POST /gateways/{id}/test_ports/
        """
        gateway = self.get_object()
        ports = request.data.get('ports', gateway.ports or [])
        timeout_ms = request.data.get('timeout_ms', 3000)

        if not ports:
            return Response(
                {'error': 'No ports specified'},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = []
        for port in ports:
            success, latency, error = self._tcp_test(gateway.host, port, timeout_ms)
            results.append({
                'port': port,
                'ok': success,
                'latency_ms': latency,
                'error': error
            })

        # Update gateway with results
        gateway.last_tcp_result = results
        gateway.save(update_fields=['last_tcp_result', 'updated_at'])

        open_ports = sum(1 for r in results if r['ok'])
        return Response({
            'gateway_id': str(gateway.id),
            'gateway_name': gateway.name,
            'host': gateway.host,
            'total_ports': len(results),
            'open_ports': open_ports,
            'results': results
        })

    def _ping_host(self, host, timeout_ms=3000):
        """
        Ping a host.

        Returns:
            Tuple of (success, latency_ms, error_message)
        """
        timeout_sec = timeout_ms / 1000

        try:
            if platform.system().lower() == 'windows':
                cmd = ['ping', '-n', '1', '-w', str(timeout_ms), host]
            else:
                cmd = ['ping', '-c', '1', '-W', str(int(timeout_sec)), host]

            start = time.perf_counter()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec + 1
            )
            latency = int((time.perf_counter() - start) * 1000)

            if result.returncode == 0:
                return True, latency, ''
            else:
                return False, 0, 'Host unreachable'

        except subprocess.TimeoutExpired:
            return False, 0, 'Ping timeout'
        except Exception as e:
            return False, 0, str(e)

    def _tcp_test(self, host, port, timeout_ms=3000):
        """
        Test TCP connection to a host:port.

        Returns:
            Tuple of (success, latency_ms, error_message)
        """
        start = time.perf_counter()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout_ms / 1000)
            sock.connect((host, int(port)))
            sock.close()
            latency = int((time.perf_counter() - start) * 1000)
            return True, latency, ''

        except socket.timeout:
            return False, 0, 'Connection timeout'
        except socket.error as e:
            return False, 0, str(e)
        except Exception as e:
            return False, 0, str(e)
