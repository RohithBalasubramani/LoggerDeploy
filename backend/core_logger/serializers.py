from rest_framework import serializers
from .models import (
    Schema, SchemaField, StorageTarget, Device, ModbusConfig, OpcuaConfig,
    Gateway, DeviceTable, FieldMapping, Job, JobTrigger, JobRun
)


# =============================================================================
# SCHEMA SERIALIZERS
# =============================================================================

class SchemaFieldSerializer(serializers.ModelSerializer):
    """Serializer for schema field definitions"""

    class Meta:
        model = SchemaField
        fields = ['id', 'key', 'field_type', 'unit', 'scale', 'description']
        read_only_fields = ['id']


class SchemaSerializer(serializers.ModelSerializer):
    """Serializer for schemas with nested fields"""
    fields = SchemaFieldSerializer(many=True, required=False)

    class Meta:
        model = Schema
        fields = ['id', 'name', 'description', 'fields', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        fields_data = validated_data.pop('fields', [])
        schema = Schema.objects.create(**validated_data)
        for field_data in fields_data:
            SchemaField.objects.create(schema=schema, **field_data)
        return schema

    def update(self, instance, validated_data):
        fields_data = validated_data.pop('fields', None)

        # Update schema fields
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.save()

        # Update nested fields if provided
        if fields_data is not None:
            # Remove existing fields and recreate
            instance.fields.all().delete()
            for field_data in fields_data:
                SchemaField.objects.create(schema=instance, **field_data)

        return instance


class SchemaListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for schema lists"""
    field_count = serializers.SerializerMethodField()

    class Meta:
        model = Schema
        fields = ['id', 'name', 'description', 'field_count', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_field_count(self, obj):
        return obj.fields.count()


# =============================================================================
# STORAGE TARGET SERIALIZERS
# =============================================================================

class StorageTargetSerializer(serializers.ModelSerializer):
    """Serializer for storage target configurations"""

    class Meta:
        model = StorageTarget
        fields = [
            'id', 'name', 'provider', 'connection_string', 'is_default',
            'status', 'last_error', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'last_error', 'created_at', 'updated_at']


class StorageTargetTestSerializer(serializers.Serializer):
    """Serializer for testing storage target connection"""
    provider = serializers.CharField()
    connection_string = serializers.CharField()


# =============================================================================
# DEVICE SERIALIZERS
# =============================================================================

class ModbusConfigSerializer(serializers.ModelSerializer):
    """Serializer for Modbus TCP configuration"""

    class Meta:
        model = ModbusConfig
        fields = ['host', 'port', 'unit_id', 'timeout_ms', 'retries']


class OpcuaConfigSerializer(serializers.ModelSerializer):
    """Serializer for OPC UA configuration"""
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = OpcuaConfig
        fields = [
            'endpoint', 'auth_type', 'username', 'password',
            'security_policy', 'security_mode'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def to_representation(self, instance):
        """Redact password in responses"""
        ret = super().to_representation(instance)
        if instance.password:
            ret['password'] = '***'
        return ret


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer for PLC devices with protocol-specific config"""
    modbus_config = ModbusConfigSerializer(required=False, allow_null=True)
    opcua_config = OpcuaConfigSerializer(required=False, allow_null=True)

    class Meta:
        model = Device
        fields = [
            'id', 'name', 'protocol', 'status', 'latency_ms', 'last_error',
            'auto_reconnect', 'modbus_config', 'opcua_config',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'latency_ms', 'last_error', 'created_at', 'updated_at']

    def validate(self, data):
        """Ensure correct config is provided for protocol"""
        protocol = data.get('protocol', getattr(self.instance, 'protocol', None))
        modbus_config = data.get('modbus_config')
        opcua_config = data.get('opcua_config')

        if protocol == 'modbus' and not modbus_config and not self.instance:
            raise serializers.ValidationError({
                'modbus_config': 'Modbus configuration is required for Modbus devices.'
            })
        if protocol == 'opcua' and not opcua_config and not self.instance:
            raise serializers.ValidationError({
                'opcua_config': 'OPC UA configuration is required for OPC UA devices.'
            })

        return data

    def create(self, validated_data):
        modbus_data = validated_data.pop('modbus_config', None)
        opcua_data = validated_data.pop('opcua_config', None)

        device = Device.objects.create(**validated_data)

        if modbus_data and device.protocol == 'modbus':
            ModbusConfig.objects.create(device=device, **modbus_data)
        if opcua_data and device.protocol == 'opcua':
            OpcuaConfig.objects.create(device=device, **opcua_data)

        return device

    def update(self, instance, validated_data):
        modbus_data = validated_data.pop('modbus_config', None)
        opcua_data = validated_data.pop('opcua_config', None)

        # Update device fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update protocol config
        if modbus_data and instance.protocol == 'modbus':
            ModbusConfig.objects.update_or_create(
                device=instance,
                defaults=modbus_data
            )
        if opcua_data and instance.protocol == 'opcua':
            OpcuaConfig.objects.update_or_create(
                device=instance,
                defaults=opcua_data
            )

        return instance


class DeviceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for device lists"""

    class Meta:
        model = Device
        fields = ['id', 'name', 'protocol', 'status', 'latency_ms', 'auto_reconnect']
        read_only_fields = ['id', 'status', 'latency_ms']


# =============================================================================
# GATEWAY SERIALIZERS
# =============================================================================

class GatewaySerializer(serializers.ModelSerializer):
    """Serializer for network gateways"""

    class Meta:
        model = Gateway
        fields = [
            'id', 'name', 'host', 'adapter_id', 'ports', 'status',
            'last_ping_ms', 'last_tcp_result', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'last_ping_ms', 'last_tcp_result', 'created_at', 'updated_at']


# =============================================================================
# FIELD MAPPING SERIALIZERS
# =============================================================================

class FieldMappingSerializer(serializers.ModelSerializer):
    """Serializer for field-to-address mappings"""

    class Meta:
        model = FieldMapping
        fields = [
            'id', 'field_key', 'protocol', 'address', 'data_type',
            'scale', 'deadband', 'byte_order', 'poll_interval_ms'
        ]
        read_only_fields = ['id']


class FieldMappingBulkSerializer(serializers.Serializer):
    """Serializer for bulk mapping operations"""
    mappings = FieldMappingSerializer(many=True)


# =============================================================================
# DEVICE TABLE SERIALIZERS
# =============================================================================

class DeviceTableSerializer(serializers.ModelSerializer):
    """Serializer for device tables"""
    mappings = FieldMappingSerializer(many=True, read_only=True)
    schema_name = serializers.CharField(source='schema.name', read_only=True)
    device_name = serializers.CharField(source='device.name', read_only=True, allow_null=True)
    storage_target_name = serializers.CharField(source='storage_target.name', read_only=True, allow_null=True)

    class Meta:
        model = DeviceTable
        fields = [
            'id', 'name', 'schema', 'schema_name', 'storage_target', 'storage_target_name',
            'device', 'device_name', 'status', 'mapping_health', 'last_migrated_at',
            'last_error', 'mappings', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'mapping_health', 'last_migrated_at',
            'last_error', 'created_at', 'updated_at'
        ]


class DeviceTableListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for device table lists"""
    schema_name = serializers.CharField(source='schema.name', read_only=True)
    device_name = serializers.CharField(source='device.name', read_only=True, allow_null=True)

    class Meta:
        model = DeviceTable
        fields = [
            'id', 'name', 'schema_name', 'device_name', 'status', 'mapping_health'
        ]
        read_only_fields = ['id', 'status', 'mapping_health']


class DeviceTableCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating device tables"""

    class Meta:
        model = DeviceTable
        fields = ['id', 'name', 'schema', 'storage_target', 'device']
        read_only_fields = ['id']


# =============================================================================
# JOB SERIALIZERS
# =============================================================================

class JobTriggerSerializer(serializers.ModelSerializer):
    """Serializer for job trigger conditions"""

    class Meta:
        model = JobTrigger
        fields = ['id', 'field', 'operator', 'value', 'deadband', 'cooldown_ms']
        read_only_fields = ['id']


class JobRunSerializer(serializers.ModelSerializer):
    """Serializer for job execution history (read-only)"""

    class Meta:
        model = JobRun
        fields = [
            'id', 'started_at', 'stopped_at', 'duration_ms', 'rows_written',
            'reads_count', 'read_errors', 'write_errors', 'avg_latency_ms',
            'p95_latency_ms', 'error_log'
        ]
        read_only_fields = fields


class JobSerializer(serializers.ModelSerializer):
    """Serializer for logging jobs with nested triggers"""
    triggers = JobTriggerSerializer(many=True, required=False)
    table_names = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id', 'name', 'job_type', 'tables', 'table_names', 'interval_ms',
            'enabled', 'status', 'batch_size', 'triggers', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']

    def get_table_names(self, obj):
        return list(obj.tables.values_list('name', flat=True))

    def create(self, validated_data):
        triggers_data = validated_data.pop('triggers', [])
        tables = validated_data.pop('tables', [])

        job = Job.objects.create(**validated_data)
        job.tables.set(tables)

        for trigger_data in triggers_data:
            JobTrigger.objects.create(job=job, **trigger_data)

        return job

    def update(self, instance, validated_data):
        triggers_data = validated_data.pop('triggers', None)
        tables = validated_data.pop('tables', None)

        # Update job fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update tables if provided
        if tables is not None:
            instance.tables.set(tables)

        # Update triggers if provided
        if triggers_data is not None:
            instance.triggers.all().delete()
            for trigger_data in triggers_data:
                JobTrigger.objects.create(job=instance, **trigger_data)

        return instance


class JobListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for job lists"""
    table_count = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = ['id', 'name', 'job_type', 'interval_ms', 'enabled', 'status', 'table_count']
        read_only_fields = ['id', 'status']

    def get_table_count(self, obj):
        return obj.tables.count()


class JobMetricsSummarySerializer(serializers.Serializer):
    """Serializer for job metrics summary"""
    job_id = serializers.UUIDField()
    job_name = serializers.CharField()
    status = serializers.CharField()
    total_runs = serializers.IntegerField()
    total_rows = serializers.IntegerField()
    total_errors = serializers.IntegerField()
    avg_latency_ms = serializers.FloatField(allow_null=True)
    last_run_at = serializers.DateTimeField(allow_null=True)


# =============================================================================
# NETWORKING SERIALIZERS
# =============================================================================

class PingRequestSerializer(serializers.Serializer):
    """Serializer for ping requests"""
    host = serializers.CharField()
    timeout_ms = serializers.IntegerField(default=3000, required=False)


class TcpTestRequestSerializer(serializers.Serializer):
    """Serializer for TCP connection test requests"""
    host = serializers.CharField()
    port = serializers.IntegerField()
    timeout_ms = serializers.IntegerField(default=3000, required=False)


class ModbusTestRequestSerializer(serializers.Serializer):
    """Serializer for Modbus test requests"""
    host = serializers.CharField()
    port = serializers.IntegerField(default=502)
    unit_id = serializers.IntegerField(default=1)
    address = serializers.IntegerField()
    count = serializers.IntegerField(default=1)
    timeout_ms = serializers.IntegerField(default=3000, required=False)


class OpcuaTestRequestSerializer(serializers.Serializer):
    """Serializer for OPC UA test requests"""
    endpoint = serializers.CharField()
    node_id = serializers.CharField(required=False, allow_blank=True)
    auth_type = serializers.CharField(default='Anonymous', required=False)
    username = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(required=False, allow_blank=True)


# =============================================================================
# HEALTH SERIALIZERS
# =============================================================================

class HealthSerializer(serializers.Serializer):
    """Serializer for health check response"""
    status = serializers.CharField()
    agent = serializers.CharField()
    version = serializers.CharField()
