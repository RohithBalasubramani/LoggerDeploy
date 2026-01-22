"""
OPC UA Service

Handles client pooling, node reads, and endpoint browsing
for OPC UA communication with PLCs.
"""

import threading
import logging
import time
from typing import Dict, Any, Optional, Tuple, List, Union

logger = logging.getLogger(__name__)


class OpcuaService:
    """
    Singleton service for OPC UA communication.

    Provides client pooling, node caching, and automatic reconnection.
    """

    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._clients: Dict[str, Any] = {}
        self._nodes: Dict[Tuple[str, str], Any] = {}
        self._client_lock = threading.RLock()
        self._initialized = True
        logger.info("OpcuaService initialized")

    def _normalize_endpoint(self, endpoint: str) -> str:
        """Normalize OPC UA endpoint URL."""
        # Replace 0.0.0.0 with localhost
        if '0.0.0.0' in endpoint:
            endpoint = endpoint.replace('0.0.0.0', '127.0.0.1')
        return endpoint

    def _get_client(
        self,
        endpoint: str,
        auth_type: str = 'Anonymous',
        username: str = '',
        password: str = ''
    ):
        """
        Get or create an OPC UA client for the given endpoint.

        Uses connection pooling to reuse existing connections.
        """
        endpoint = self._normalize_endpoint(endpoint)

        with self._client_lock:
            client = self._clients.get(endpoint)
            if client is not None:
                return client

            # Create new client
            try:
                from opcua import Client
            except ImportError:
                raise RuntimeError("opcua package is not installed")

            client = Client(endpoint)

            # Set authentication if required
            if auth_type.lower() not in ('anonymous', ''):
                if username and password:
                    client.set_user(username)
                    client.set_password(password)

            try:
                client.connect()
                self._clients[endpoint] = client
                logger.info(f"OPC UA connected to {endpoint}")
                return client
            except Exception as e:
                raise ConnectionError(f"Failed to connect to OPC UA endpoint {endpoint}: {e}")

    def _drop_client(self, endpoint: str) -> None:
        """Close and remove a client from the pool."""
        endpoint = self._normalize_endpoint(endpoint)

        with self._client_lock:
            client = self._clients.pop(endpoint, None)
            if client:
                # Remove cached nodes for this endpoint
                for key in list(self._nodes.keys()):
                    if key[0] == endpoint:
                        self._nodes.pop(key, None)

                try:
                    client.disconnect()
                    logger.info(f"OPC UA disconnected from {endpoint}")
                except Exception as e:
                    logger.warning(f"Error closing OPC UA client: {e}")

    def disconnect(self, endpoint: str) -> None:
        """Explicitly disconnect from an endpoint."""
        self._drop_client(endpoint)

    def disconnect_all(self) -> None:
        """Disconnect all OPC UA clients."""
        with self._client_lock:
            for endpoint in list(self._clients.keys()):
                self._drop_client(endpoint)

    def test_connection(
        self,
        endpoint: str,
        node_id: str = '',
        auth_type: str = 'Anonymous',
        username: str = '',
        password: str = ''
    ) -> Tuple[bool, int, str, Any]:
        """
        Test connection to an OPC UA endpoint.

        Args:
            endpoint: OPC UA endpoint URL
            node_id: Optional node ID to read for verification
            auth_type: Authentication type ('Anonymous' or 'UserPassword')
            username: Username for authentication
            password: Password for authentication

        Returns:
            Tuple of (success, latency_ms, error_message, value)
        """
        try:
            from opcua import Client
        except ImportError:
            return False, 0, "OPCUA_PKG_MISSING", None

        endpoint = self._normalize_endpoint(endpoint)
        start = time.perf_counter()

        try:
            client = Client(endpoint)

            if auth_type.lower() not in ('anonymous', ''):
                if username and password:
                    client.set_user(username)
                    client.set_password(password)

            client.connect()

            value = None
            if node_id:
                node = client.get_node(node_id)
                value = node.get_value()

            client.disconnect()

            latency = int((time.perf_counter() - start) * 1000)
            return True, latency, "", value

        except Exception as e:
            latency = int((time.perf_counter() - start) * 1000)
            return False, latency, str(e), None

    def _get_node(self, endpoint: str, node_id: str, client=None):
        """Get or cache a node object."""
        endpoint = self._normalize_endpoint(endpoint)
        key = (endpoint, node_id)

        with self._client_lock:
            node = self._nodes.get(key)
            if node is not None:
                return node

        if client is None:
            client = self._get_client(endpoint)

        node = client.get_node(node_id)

        with self._client_lock:
            self._nodes[key] = node

        return node

    def read_value(
        self,
        endpoint: str,
        node_id: str,
        auth_type: str = 'Anonymous',
        username: str = '',
        password: str = '',
        scale: float = 1.0
    ) -> Any:
        """
        Read a value from an OPC UA node.

        Args:
            endpoint: OPC UA endpoint URL
            node_id: Node identifier (e.g., "ns=2;i=12" or "ns=1;s=Temperature")
            auth_type: Authentication type
            username: Username for authentication
            password: Password for authentication
            scale: Scale factor to apply to numeric values

        Returns:
            Node value
        """
        try:
            client = self._get_client(endpoint, auth_type, username, password)
            node = self._get_node(endpoint, node_id, client)
            value = node.get_value()

            # Apply scale to numeric values
            if isinstance(value, (int, float)) and scale != 1.0:
                value = value * scale

            return value

        except Exception as e:
            # Drop client on error to force reconnect
            self._drop_client(endpoint)
            raise

    def read_multiple(
        self,
        endpoint: str,
        node_ids: List[str],
        auth_type: str = 'Anonymous',
        username: str = '',
        password: str = ''
    ) -> Dict[str, Any]:
        """
        Read multiple values from OPC UA nodes.

        Args:
            endpoint: OPC UA endpoint URL
            node_ids: List of node identifiers
            auth_type: Authentication type
            username: Username for authentication
            password: Password for authentication

        Returns:
            Dictionary of node_id -> value
        """
        results = {}
        client = self._get_client(endpoint, auth_type, username, password)

        for node_id in node_ids:
            try:
                node = self._get_node(endpoint, node_id, client)
                results[node_id] = node.get_value()
            except Exception as e:
                logger.warning(f"Failed to read node {node_id}: {e}")
                results[node_id] = None

        return results

    def browse_nodes(
        self,
        endpoint: str,
        root_node_id: str = '',
        max_depth: int = 2,
        auth_type: str = 'Anonymous',
        username: str = '',
        password: str = ''
    ) -> List[Dict[str, Any]]:
        """
        Browse OPC UA nodes starting from a root node.

        Args:
            endpoint: OPC UA endpoint URL
            root_node_id: Starting node ID (empty for root)
            max_depth: Maximum depth to browse
            auth_type: Authentication type
            username: Username for authentication
            password: Password for authentication

        Returns:
            List of node information dictionaries
        """
        try:
            from opcua import Client, ua
        except ImportError:
            raise RuntimeError("opcua package is not installed")

        endpoint = self._normalize_endpoint(endpoint)
        client = Client(endpoint)

        if auth_type.lower() not in ('anonymous', ''):
            if username and password:
                client.set_user(username)
                client.set_password(password)

        try:
            client.connect()

            if root_node_id:
                root = client.get_node(root_node_id)
            else:
                root = client.get_root_node()

            nodes = self._browse_recursive(root, max_depth, 0)
            client.disconnect()
            return nodes

        except Exception as e:
            try:
                client.disconnect()
            except:
                pass
            raise

    def _browse_recursive(self, node, max_depth: int, current_depth: int) -> List[Dict[str, Any]]:
        """Recursively browse nodes."""
        results = []

        try:
            browse_name = node.get_browse_name()
            node_class = node.get_node_class()

            node_info = {
                'node_id': node.nodeid.to_string(),
                'browse_name': browse_name.Name,
                'namespace': browse_name.NamespaceIndex,
                'node_class': str(node_class),
                'children': []
            }

            # Try to get value for variable nodes
            if 'Variable' in str(node_class):
                try:
                    node_info['value'] = node.get_value()
                    node_info['data_type'] = str(node.get_data_type_as_variant_type())
                except:
                    pass

            # Browse children if within depth limit
            if current_depth < max_depth:
                try:
                    children = node.get_children()
                    for child in children:
                        child_info = self._browse_recursive(child, max_depth, current_depth + 1)
                        if child_info:
                            node_info['children'].extend(child_info)
                except:
                    pass

            results.append(node_info)

        except Exception as e:
            logger.warning(f"Error browsing node: {e}")

        return results


# Singleton instance
opcua_service = OpcuaService()
