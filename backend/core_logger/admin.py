from django.contrib import admin
from .models import (
    Schema, SchemaField, StorageTarget, Device, ModbusConfig, OpcuaConfig,
    Gateway, DeviceTable, FieldMapping, Job, JobTrigger, JobRun
)


class SchemaFieldInline(admin.TabularInline):
    model = SchemaField
    extra = 1


@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']
    inlines = [SchemaFieldInline]


@admin.register(SchemaField)
class SchemaFieldAdmin(admin.ModelAdmin):
    list_display = ['key', 'schema', 'field_type', 'unit', 'scale']
    list_filter = ['schema', 'field_type']
    search_fields = ['key', 'schema__name']


@admin.register(StorageTarget)
class StorageTargetAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider', 'is_default', 'status', 'created_at']
    list_filter = ['provider', 'is_default', 'status']
    search_fields = ['name']


class ModbusConfigInline(admin.StackedInline):
    model = ModbusConfig
    can_delete = False


class OpcuaConfigInline(admin.StackedInline):
    model = OpcuaConfig
    can_delete = False


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['name', 'protocol', 'status', 'latency_ms', 'auto_reconnect']
    list_filter = ['protocol', 'status', 'auto_reconnect']
    search_fields = ['name']
    inlines = [ModbusConfigInline, OpcuaConfigInline]


@admin.register(ModbusConfig)
class ModbusConfigAdmin(admin.ModelAdmin):
    list_display = ['device', 'host', 'port', 'unit_id', 'timeout_ms']
    search_fields = ['device__name', 'host']


@admin.register(OpcuaConfig)
class OpcuaConfigAdmin(admin.ModelAdmin):
    list_display = ['device', 'endpoint', 'auth_type']
    search_fields = ['device__name', 'endpoint']


@admin.register(Gateway)
class GatewayAdmin(admin.ModelAdmin):
    list_display = ['name', 'host', 'status', 'last_ping_ms', 'created_at']
    list_filter = ['status']
    search_fields = ['name', 'host']


class FieldMappingInline(admin.TabularInline):
    model = FieldMapping
    extra = 1


@admin.register(DeviceTable)
class DeviceTableAdmin(admin.ModelAdmin):
    list_display = ['name', 'schema', 'storage_target', 'device', 'status', 'mapping_health']
    list_filter = ['status', 'mapping_health', 'schema', 'storage_target']
    search_fields = ['name']
    inlines = [FieldMappingInline]


@admin.register(FieldMapping)
class FieldMappingAdmin(admin.ModelAdmin):
    list_display = ['field_key', 'device_table', 'protocol', 'address', 'data_type', 'byte_order']
    list_filter = ['protocol', 'data_type', 'device_table']
    search_fields = ['field_key', 'device_table__name']


class JobTriggerInline(admin.TabularInline):
    model = JobTrigger
    extra = 1


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['name', 'job_type', 'interval_ms', 'enabled', 'status', 'created_at']
    list_filter = ['job_type', 'enabled', 'status']
    search_fields = ['name']
    filter_horizontal = ['tables']
    inlines = [JobTriggerInline]


@admin.register(JobTrigger)
class JobTriggerAdmin(admin.ModelAdmin):
    list_display = ['job', 'field', 'operator', 'value', 'deadband', 'cooldown_ms']
    list_filter = ['operator', 'job']
    search_fields = ['field', 'job__name']


@admin.register(JobRun)
class JobRunAdmin(admin.ModelAdmin):
    list_display = ['job', 'started_at', 'stopped_at', 'duration_ms', 'rows_written', 'read_errors', 'write_errors']
    list_filter = ['job']
    search_fields = ['job__name']
    readonly_fields = ['started_at', 'stopped_at', 'duration_ms', 'rows_written', 'reads_count',
                       'read_errors', 'write_errors', 'avg_latency_ms', 'p95_latency_ms', 'error_log']
