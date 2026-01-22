from django.db import models
import uuid


# =============================================================================
# CHOICES
# =============================================================================

class ProtocolType(models.TextChoices):
    MODBUS = 'modbus', 'Modbus TCP'
    OPCUA = 'opcua', 'OPC UA'


class DeviceStatus(models.TextChoices):
    DISCONNECTED = 'disconnected', 'Disconnected'
    CONNECTED = 'connected', 'Connected'
    ERROR = 'error', 'Error'


class JobType(models.TextChoices):
    CONTINUOUS = 'continuous', 'Continuous'
    TRIGGER = 'trigger', 'Trigger'


class JobStatus(models.TextChoices):
    STOPPED = 'stopped', 'Stopped'
    RUNNING = 'running', 'Running'
    PAUSED = 'paused', 'Paused'


class DataType(models.TextChoices):
    BOOL = 'bool', 'Boolean'
    INT = 'int', 'Integer'
    FLOAT = 'float', 'Float'
    STRING = 'string', 'String'


class ByteOrder(models.TextChoices):
    ABCD = 'ABCD', 'Big-endian (ABCD)'
    DCBA = 'DCBA', 'Little-endian (DCBA)'
    BADC = 'BADC', 'Mid-big (BADC)'
    CDAB = 'CDAB', 'Mid-little (CDAB)'


class TriggerOperator(models.TextChoices):
    CHANGE = 'change', 'Change'
    GT = '>', 'Greater than'
    GTE = '>=', 'Greater than or equal'
    LT = '<', 'Less than'
    LTE = '<=', 'Less than or equal'
    EQ = '==', 'Equal'
    NEQ = '!=', 'Not equal'
    RISING = 'rising', 'Rising edge'
    FALLING = 'falling', 'Falling edge'


class StorageProvider(models.TextChoices):
    SQLITE = 'sqlite', 'SQLite'
    POSTGRES = 'postgres', 'PostgreSQL'
    MYSQL = 'mysql', 'MySQL'
    MSSQL = 'mssql', 'SQL Server'


class MappingHealth(models.TextChoices):
    UNMAPPED = 'unmapped', 'Unmapped'
    PARTIAL = 'partial', 'Partially Mapped'
    MAPPED = 'mapped', 'Fully Mapped'


class TableStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    MIGRATED = 'migrated', 'Migrated'
    ERROR = 'error', 'Error'


# =============================================================================
# SCHEMA MODELS
# =============================================================================

class Schema(models.Model):
    """Data template defining a device type (e.g., LT Panel, Inverter)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'app_schemas'
        ordering = ['name']

    def __str__(self):
        return self.name


class SchemaField(models.Model):
    """Individual field within a schema"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schema = models.ForeignKey(
        Schema,
        on_delete=models.CASCADE,
        related_name='fields'
    )
    key = models.CharField(max_length=255)
    field_type = models.CharField(
        max_length=20,
        choices=DataType.choices,
        default=DataType.FLOAT
    )
    unit = models.CharField(max_length=50, blank=True, default='')
    scale = models.FloatField(default=1.0)
    description = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'app_schema_fields'
        unique_together = ['schema', 'key']
        ordering = ['schema', 'key']

    def __str__(self):
        return f"{self.schema.name}.{self.key}"


# =============================================================================
# STORAGE TARGET MODELS
# =============================================================================

class StorageTarget(models.Model):
    """External database connection configuration for logging data"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    provider = models.CharField(
        max_length=20,
        choices=StorageProvider.choices,
        default=StorageProvider.SQLITE
    )
    connection_string = models.TextField()
    is_default = models.BooleanField(default=False)
    status = models.CharField(max_length=50, default='unknown')
    last_error = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'app_storage_targets'
        ordering = ['-is_default', 'name']

    def __str__(self):
        return f"{self.name} ({self.provider})"

    def save(self, *args, **kwargs):
        # Ensure only one default target
        if self.is_default:
            StorageTarget.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


# =============================================================================
# DEVICE MODELS
# =============================================================================

class Device(models.Model):
    """PLC device configuration"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    protocol = models.CharField(
        max_length=20,
        choices=ProtocolType.choices
    )
    status = models.CharField(
        max_length=20,
        choices=DeviceStatus.choices,
        default=DeviceStatus.DISCONNECTED
    )
    latency_ms = models.IntegerField(null=True, blank=True)
    last_error = models.TextField(blank=True, default='')
    auto_reconnect = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'app_devices'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.protocol})"


class ModbusConfig(models.Model):
    """Modbus TCP specific connection parameters"""
    device = models.OneToOneField(
        Device,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='modbus_config'
    )
    host = models.CharField(max_length=255)
    port = models.IntegerField(default=502)
    unit_id = models.IntegerField(default=1)
    timeout_ms = models.IntegerField(default=3000)
    retries = models.IntegerField(default=3)

    class Meta:
        db_table = 'app_modbus_configs'

    def __str__(self):
        return f"Modbus {self.host}:{self.port}"


class OpcuaConfig(models.Model):
    """OPC UA specific connection parameters"""
    device = models.OneToOneField(
        Device,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='opcua_config'
    )
    endpoint = models.CharField(max_length=500)
    auth_type = models.CharField(max_length=50, default='Anonymous')
    username = models.CharField(max_length=255, blank=True, default='')
    password = models.CharField(max_length=255, blank=True, default='')
    security_policy = models.CharField(max_length=100, blank=True, default='')
    security_mode = models.CharField(max_length=100, blank=True, default='')

    class Meta:
        db_table = 'app_opcua_configs'

    def __str__(self):
        return f"OPC UA {self.endpoint}"


# =============================================================================
# GATEWAY MODELS
# =============================================================================

class Gateway(models.Model):
    """Network gateway configuration for connectivity"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    host = models.CharField(max_length=255)
    adapter_id = models.CharField(max_length=255, blank=True, default='')
    ports = models.JSONField(default=list)  # List of port numbers
    status = models.CharField(max_length=50, default='unknown')
    last_ping_ms = models.IntegerField(null=True, blank=True)
    last_tcp_result = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'app_gateways'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.host})"


# =============================================================================
# DEVICE TABLE & MAPPING MODELS
# =============================================================================

class DeviceTable(models.Model):
    """Logical table instance bound to a schema and device"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    schema = models.ForeignKey(
        Schema,
        on_delete=models.PROTECT,
        related_name='device_tables'
    )
    storage_target = models.ForeignKey(
        StorageTarget,
        on_delete=models.PROTECT,
        related_name='device_tables',
        null=True,
        blank=True
    )
    device = models.ForeignKey(
        Device,
        on_delete=models.SET_NULL,
        related_name='device_tables',
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=TableStatus.choices,
        default=TableStatus.PENDING
    )
    mapping_health = models.CharField(
        max_length=20,
        choices=MappingHealth.choices,
        default=MappingHealth.UNMAPPED
    )
    last_migrated_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'app_device_tables'
        unique_together = ['name', 'storage_target']
        ordering = ['name']

    def __str__(self):
        return self.name


class FieldMapping(models.Model):
    """Maps a table column to a PLC address"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device_table = models.ForeignKey(
        DeviceTable,
        on_delete=models.CASCADE,
        related_name='mappings'
    )
    field_key = models.CharField(max_length=255)
    protocol = models.CharField(
        max_length=20,
        choices=ProtocolType.choices
    )
    address = models.CharField(max_length=255)  # e.g., "40001" or "ns=2;i=12"
    data_type = models.CharField(
        max_length=20,
        choices=DataType.choices,
        default=DataType.FLOAT
    )
    scale = models.FloatField(default=1.0)
    deadband = models.FloatField(default=0.0)
    byte_order = models.CharField(
        max_length=10,
        choices=ByteOrder.choices,
        default=ByteOrder.ABCD,
        blank=True
    )
    poll_interval_ms = models.IntegerField(null=True, blank=True)  # Override job interval

    class Meta:
        db_table = 'app_field_mappings'
        unique_together = ['device_table', 'field_key']
        ordering = ['device_table', 'field_key']

    def __str__(self):
        return f"{self.device_table.name}.{self.field_key} -> {self.address}"


# =============================================================================
# JOB MODELS
# =============================================================================

class Job(models.Model):
    """Logging job configuration"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    job_type = models.CharField(
        max_length=20,
        choices=JobType.choices,
        default=JobType.CONTINUOUS
    )
    tables = models.ManyToManyField(
        DeviceTable,
        related_name='jobs',
        blank=True
    )
    interval_ms = models.IntegerField(default=1000)
    enabled = models.BooleanField(default=True)
    status = models.CharField(
        max_length=20,
        choices=JobStatus.choices,
        default=JobStatus.STOPPED
    )
    batch_size = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'app_jobs'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.job_type})"


class JobTrigger(models.Model):
    """Trigger condition for trigger-based jobs"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='triggers'
    )
    field = models.CharField(max_length=255)
    operator = models.CharField(
        max_length=20,
        choices=TriggerOperator.choices,
        default=TriggerOperator.CHANGE
    )
    value = models.FloatField(null=True, blank=True)
    deadband = models.FloatField(default=0.0)
    cooldown_ms = models.IntegerField(default=0)

    class Meta:
        db_table = 'app_job_triggers'
        ordering = ['job', 'field']

    def __str__(self):
        return f"{self.job.name}: {self.field} {self.operator} {self.value}"


class JobRun(models.Model):
    """Job execution history record"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='runs'
    )
    started_at = models.DateTimeField()
    stopped_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.IntegerField(null=True, blank=True)
    rows_written = models.IntegerField(default=0)
    reads_count = models.IntegerField(default=0)
    read_errors = models.IntegerField(default=0)
    write_errors = models.IntegerField(default=0)
    avg_latency_ms = models.FloatField(null=True, blank=True)
    p95_latency_ms = models.FloatField(null=True, blank=True)
    error_log = models.JSONField(default=list)

    class Meta:
        db_table = 'app_job_runs'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.job.name} run at {self.started_at}"
