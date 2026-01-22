"""
Networking Views

Network diagnostics: ping, TCP test, Modbus test, OPC UA test.
"""

import socket
import subprocess
import platform
import time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..serializers import (
    PingRequestSerializer, TcpTestRequestSerializer,
    ModbusTestRequestSerializer, OpcuaTestRequestSerializer
)
from ..permissions import IsNeuractAdminForUnsafeMethods
from ..services import ModbusService, OpcuaService


class NetworkingViewSet(APIView):
    """
    Network diagnostics endpoints.

    POST /networking/ping/ - ICMP ping test
    POST /networking/tcp_test/ - TCP connection test
    POST /networking/modbus/test/ - Modbus register read test
    POST /networking/opcua/test/ - OPC UA endpoint test
    POST /networking/opcua/browse/ - OPC UA node browser
    GET /networking/nics/ - List network interfaces
    """
    permission_classes = [IsNeuractAdminForUnsafeMethods]


class PingView(APIView):
    """ICMP ping test."""
    permission_classes = [IsNeuractAdminForUnsafeMethods]

    def post(self, request):
        serializer = PingRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        host = serializer.validated_data['host']
        timeout_ms = serializer.validated_data.get('timeout_ms', 3000)
        timeout_sec = timeout_ms / 1000

        try:
            # Platform-specific ping command
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
                return Response({
                    'ok': True,
                    'host': host,
                    'latency_ms': latency
                })
            else:
                return Response({
                    'ok': False,
                    'host': host,
                    'error': 'Host unreachable'
                })

        except subprocess.TimeoutExpired:
            return Response({
                'ok': False,
                'host': host,
                'error': 'Ping timeout'
            })
        except Exception as e:
            return Response({
                'ok': False,
                'host': host,
                'error': str(e)
            })


class TcpTestView(APIView):
    """TCP connection test."""
    permission_classes = [IsNeuractAdminForUnsafeMethods]

    def post(self, request):
        serializer = TcpTestRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        host = serializer.validated_data['host']
        port = serializer.validated_data['port']
        timeout_ms = serializer.validated_data.get('timeout_ms', 3000)

        start = time.perf_counter()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout_ms / 1000)
            sock.connect((host, port))
            sock.close()
            latency = int((time.perf_counter() - start) * 1000)

            return Response({
                'ok': True,
                'host': host,
                'port': port,
                'latency_ms': latency
            })

        except socket.timeout:
            return Response({
                'ok': False,
                'host': host,
                'port': port,
                'error': 'Connection timeout'
            })
        except socket.error as e:
            return Response({
                'ok': False,
                'host': host,
                'port': port,
                'error': str(e)
            })


class ModbusTestView(APIView):
    """Modbus TCP register read test."""
    permission_classes = [IsNeuractAdminForUnsafeMethods]

    def post(self, request):
        serializer = ModbusTestRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        host = serializer.validated_data['host']
        port = serializer.validated_data.get('port', 502)
        unit_id = serializer.validated_data.get('unit_id', 1)
        address = serializer.validated_data['address']
        count = serializer.validated_data.get('count', 1)
        timeout_ms = serializer.validated_data.get('timeout_ms', 3000)

        start = time.perf_counter()
        try:
            registers = ModbusService().read_registers(
                host=host,
                port=port,
                address=address,
                count=count,
                unit_id=unit_id,
                register_type='holding'
            )
            latency = int((time.perf_counter() - start) * 1000)

            return Response({
                'ok': True,
                'protocol': 'modbus',
                'host': host,
                'port': port,
                'unit_id': unit_id,
                'address': address,
                'registers': registers,
                'latency_ms': latency
            })

        except Exception as e:
            latency = int((time.perf_counter() - start) * 1000)
            return Response({
                'ok': False,
                'protocol': 'modbus',
                'host': host,
                'port': port,
                'error': str(e),
                'latency_ms': latency
            })


class OpcuaTestView(APIView):
    """OPC UA endpoint test."""
    permission_classes = [IsNeuractAdminForUnsafeMethods]

    def post(self, request):
        serializer = OpcuaTestRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        endpoint = serializer.validated_data['endpoint']
        node_id = serializer.validated_data.get('node_id', '')
        auth_type = serializer.validated_data.get('auth_type', 'Anonymous')
        username = serializer.validated_data.get('username', '')
        password = serializer.validated_data.get('password', '')

        success, latency, error, value = OpcuaService().test_connection(
            endpoint=endpoint,
            node_id=node_id,
            auth_type=auth_type,
            username=username,
            password=password
        )

        response_data = {
            'ok': success,
            'protocol': 'opcua',
            'endpoint': endpoint,
            'latency_ms': latency
        }

        if success:
            if value is not None:
                response_data['value'] = value
        else:
            response_data['error'] = error

        return Response(response_data)


class OpcuaBrowseView(APIView):
    """OPC UA node browser."""
    permission_classes = [IsNeuractAdminForUnsafeMethods]

    def post(self, request):
        endpoint = request.data.get('endpoint', '')
        root_node_id = request.data.get('root_node_id', '')
        max_depth = request.data.get('max_depth', 2)
        auth_type = request.data.get('auth_type', 'Anonymous')
        username = request.data.get('username', '')
        password = request.data.get('password', '')

        if not endpoint:
            return Response(
                {'error': 'endpoint is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            nodes = OpcuaService().browse_nodes(
                endpoint=endpoint,
                root_node_id=root_node_id,
                max_depth=max_depth,
                auth_type=auth_type,
                username=username,
                password=password
            )

            return Response({
                'ok': True,
                'endpoint': endpoint,
                'nodes': nodes
            })

        except Exception as e:
            return Response({
                'ok': False,
                'endpoint': endpoint,
                'error': str(e)
            })


class NicsView(APIView):
    """List network interfaces."""
    permission_classes = [IsNeuractAdminForUnsafeMethods]

    def get(self, request):
        try:
            import psutil
            nics = []
            for name, addrs in psutil.net_if_addrs().items():
                nic_info = {'name': name, 'addresses': []}
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        nic_info['addresses'].append({
                            'family': 'IPv4',
                            'address': addr.address,
                            'netmask': addr.netmask
                        })
                    elif addr.family == socket.AF_INET6:
                        nic_info['addresses'].append({
                            'family': 'IPv6',
                            'address': addr.address
                        })
                if nic_info['addresses']:
                    nics.append(nic_info)

            return Response({'nics': nics})

        except ImportError:
            # Fallback without psutil
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return Response({
                'nics': [{
                    'name': 'default',
                    'addresses': [{'family': 'IPv4', 'address': ip}]
                }]
            })
