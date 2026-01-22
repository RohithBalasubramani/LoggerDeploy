"""
Modbus TCP Service

Handles connection pooling, register reads, and data type conversions
for Modbus TCP communication with PLCs.
"""

import struct
import threading
import logging
import time
from typing import Dict, Any, Optional, Tuple, List, Union

logger = logging.getLogger(__name__)


class ModbusService:
    """
    Singleton service for Modbus TCP communication.

    Provides connection pooling, automatic reconnection, and data type handling.
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

        self._clients: Dict[Tuple[str, int], Any] = {}
        self._client_lock = threading.RLock()
        self._initialized = True
        logger.info("ModbusService initialized")

    def _get_client(self, host: str, port: int):
        """
        Get or create a Modbus client for the given host/port.

        Uses connection pooling to reuse existing connections.
        """
        key = (host, port)

        with self._client_lock:
            client = self._clients.get(key)
            if client is not None and client.connected:
                return client

            # Create new client
            try:
                from pymodbus.client import ModbusTcpClient
            except ImportError:
                raise RuntimeError("pymodbus package is not installed")

            client = ModbusTcpClient(host=host, port=port, timeout=3)
            if client.connect():
                self._clients[key] = client
                logger.info(f"Modbus connected to {host}:{port}")
                return client
            else:
                raise ConnectionError(f"Failed to connect to Modbus device at {host}:{port}")

    def _drop_client(self, host: str, port: int) -> None:
        """Close and remove a client from the pool."""
        key = (host, port)

        with self._client_lock:
            client = self._clients.pop(key, None)
            if client:
                try:
                    client.close()
                    logger.info(f"Modbus disconnected from {host}:{port}")
                except Exception as e:
                    logger.warning(f"Error closing Modbus client: {e}")

    def disconnect(self, host: str, port: int) -> None:
        """Explicitly disconnect from a device."""
        self._drop_client(host, port)

    def disconnect_all(self) -> None:
        """Disconnect all Modbus clients."""
        with self._client_lock:
            for key in list(self._clients.keys()):
                self._drop_client(*key)

    def test_connection(
        self,
        host: str,
        port: int = 502,
        unit_id: int = 1,
        timeout_ms: int = 3000
    ) -> Tuple[bool, int, str]:
        """
        Test connection to a Modbus device.

        Returns:
            Tuple of (success, latency_ms, error_message)
        """
        try:
            from pymodbus.client import ModbusTcpClient
        except ImportError:
            return False, 0, "MODBUS_PKG_MISSING"

        start = time.perf_counter()
        try:
            client = ModbusTcpClient(
                host=host,
                port=port,
                timeout=timeout_ms / 1000
            )

            if not client.connect():
                return False, 0, f"CONNECTION_FAILED: Unable to connect to {host}:{port}"

            # Try reading a register to verify communication
            # pymodbus 3.11+: read_holding_registers(address, *, count=, device_id=)
            result = client.read_holding_registers(0, count=1, device_id=unit_id)
            client.close()

            latency = int((time.perf_counter() - start) * 1000)

            if result.isError():
                return False, latency, f"READ_ERROR: {result}"

            return True, latency, ""

        except Exception as e:
            latency = int((time.perf_counter() - start) * 1000)
            return False, latency, str(e)

    def read_registers(
        self,
        host: str,
        port: int,
        address: int,
        count: int = 1,
        unit_id: int = 1,
        register_type: str = 'holding'
    ) -> List[int]:
        """
        Read raw registers from a Modbus device.

        Args:
            host: Device hostname or IP
            port: Modbus TCP port
            address: Starting register address
            count: Number of registers to read
            unit_id: Modbus unit/slave ID
            register_type: 'holding', 'input', 'coil', or 'discrete'

        Returns:
            List of register values
        """
        client = self._get_client(host, port)

        try:
            # pymodbus 3.11+: (address, *, count=, device_id=)
            if register_type == 'holding':
                result = client.read_holding_registers(address, count=count, device_id=unit_id)
            elif register_type == 'input':
                result = client.read_input_registers(address, count=count, device_id=unit_id)
            elif register_type == 'coil':
                result = client.read_coils(address, count=count, device_id=unit_id)
            elif register_type == 'discrete':
                result = client.read_discrete_inputs(address, count=count, device_id=unit_id)
            else:
                raise ValueError(f"Unknown register type: {register_type}")

            if result.isError():
                raise IOError(f"Modbus read error: {result}")

            if register_type in ('coil', 'discrete'):
                return result.bits[:count]
            return result.registers

        except Exception as e:
            # Drop client on error to force reconnect
            self._drop_client(host, port)
            raise

    def read_value(
        self,
        host: str,
        port: int,
        address: int,
        data_type: str = 'float',
        unit_id: int = 1,
        byte_order: str = 'ABCD',
        scale: float = 1.0
    ) -> Union[bool, int, float, str]:
        """
        Read and convert a value from a Modbus device.

        Args:
            host: Device hostname or IP
            port: Modbus TCP port
            address: Register address (Modbus convention: 40001 for first holding register)
            data_type: 'bool', 'int', 'float', or 'string'
            unit_id: Modbus unit/slave ID
            byte_order: 'ABCD', 'DCBA', 'BADC', or 'CDAB'
            scale: Scale factor to apply to numeric values

        Returns:
            Converted value
        """
        # Determine register type and actual address from Modbus convention
        register_type, actual_address = self._parse_address(address)

        if data_type == 'bool':
            if register_type in ('coil', 'discrete'):
                registers = self.read_registers(
                    host, port, actual_address, 1, unit_id, register_type
                )
                return bool(registers[0])
            else:
                # Read as int and check for non-zero
                registers = self.read_registers(
                    host, port, actual_address, 1, unit_id, register_type
                )
                return registers[0] != 0

        elif data_type == 'int':
            registers = self.read_registers(
                host, port, actual_address, 1, unit_id, register_type
            )
            value = self._to_signed_int(registers[0])
            return int(value * scale)

        elif data_type == 'float':
            registers = self.read_registers(
                host, port, actual_address, 2, unit_id, register_type
            )
            value = self._registers_to_float(registers, byte_order)
            return value * scale

        elif data_type == 'string':
            # Read 16 registers (32 characters max)
            registers = self.read_registers(
                host, port, actual_address, 16, unit_id, register_type
            )
            return self._registers_to_string(registers)

        else:
            raise ValueError(f"Unknown data type: {data_type}")

    def _parse_address(self, address: int) -> Tuple[str, int]:
        """
        Parse Modbus address convention to register type and actual address.

        Convention:
            0-9999: Coils (read/write, 1-bit)
            10001-19999: Discrete Inputs (read-only, 1-bit)
            30001-39999: Input Registers (read-only, 16-bit)
            40001-49999: Holding Registers (read/write, 16-bit)
        """
        if 40001 <= address <= 49999:
            return 'holding', address - 40001
        elif 30001 <= address <= 39999:
            return 'input', address - 30001
        elif 10001 <= address <= 19999:
            return 'discrete', address - 10001
        elif 0 <= address <= 9999:
            return 'coil', address
        else:
            # Default to holding register with raw address
            return 'holding', address

    def _to_signed_int(self, value: int) -> int:
        """Convert unsigned 16-bit to signed."""
        if value >= 0x8000:
            return value - 0x10000
        return value

    def _registers_to_float(self, registers: List[int], byte_order: str) -> float:
        """
        Convert two 16-bit registers to a 32-bit float.

        Args:
            registers: Two 16-bit register values
            byte_order: 'ABCD', 'DCBA', 'BADC', or 'CDAB'

        Byte order explanation:
            - ABCD: Big-endian (network order) - reg1=high word, reg2=low word
            - DCBA: Little-endian - reverse everything
            - BADC: Mid-big (byte swap within words) - swap word order
            - CDAB: Mid-little (word swap) - swap word order, little-endian unpack
        """
        if len(registers) < 2:
            raise ValueError("Need at least 2 registers for float conversion")

        reg1 = registers[0]
        reg2 = registers[1]

        # Apply byte order to convert two 16-bit registers to 32-bit float
        # All pack as big-endian, then unpack as big-endian float
        if byte_order == 'ABCD':
            # Big-endian (network order): reg1 = high word, reg2 = low word
            bytes_data = struct.pack('>HH', reg1, reg2)
        elif byte_order == 'DCBA':
            # Little-endian: reverse everything
            bytes_data = struct.pack('<HH', reg2, reg1)
        elif byte_order == 'BADC':
            # Mid-big (byte swap within words): swap word order
            bytes_data = struct.pack('>HH', reg2, reg1)
        elif byte_order == 'CDAB':
            # Mid-little (word swap): swap word order, little-endian pack
            bytes_data = struct.pack('<HH', reg1, reg2)
        else:
            # Default to big-endian
            bytes_data = struct.pack('>HH', reg1, reg2)

        # Always unpack as big-endian float
        return struct.unpack('>f', bytes_data)[0]

    def _registers_to_string(self, registers: List[int]) -> str:
        """Convert registers to ASCII string (2 chars per register)."""
        chars = []
        for reg in registers:
            high_byte = (reg >> 8) & 0xFF
            low_byte = reg & 0xFF
            if high_byte == 0:
                break
            chars.append(chr(high_byte))
            if low_byte == 0:
                break
            chars.append(chr(low_byte))
        return ''.join(chars)


# Singleton instance
modbus_service = ModbusService()
