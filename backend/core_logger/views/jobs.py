"""
Job Views

CRUD operations for logging jobs and job execution control.
"""

from django.utils import timezone
from django.db.models import Sum, Avg, Count
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Job, JobRun, JobStatus, DeviceTable
from ..serializers import JobSerializer, JobListSerializer, JobRunSerializer
from ..permissions import IsNeuractAdminForUnsafeMethods
from ..services import JobExecutor, ModbusService, OpcuaService, StorageService


class JobViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Job CRUD operations.

    GET /jobs/ - List all jobs
    POST /jobs/ - Create a new job
    GET /jobs/{id}/ - Retrieve a job
    PUT /jobs/{id}/ - Update a job
    DELETE /jobs/{id}/ - Delete a job
    POST /jobs/{id}/start/ - Start job execution
    POST /jobs/{id}/pause/ - Pause job execution
    POST /jobs/{id}/stop/ - Stop job execution
    POST /jobs/stop_all/ - Stop all running jobs
    GET /jobs/{id}/metrics/ - Get job metrics
    GET /jobs/metrics/summary/ - Get all job metrics
    GET /jobs/{id}/runs/ - Get job run history
    POST /jobs/{id}/dry_run/ - Test job without writing
    """
    queryset = Job.objects.prefetch_related('tables', 'triggers').all()
    permission_classes = [IsNeuractAdminForUnsafeMethods]

    def get_serializer_class(self):
        if self.action == 'list':
            return JobListSerializer
        return JobSerializer

    def perform_destroy(self, instance):
        """Stop job before deleting."""
        if JobExecutor().is_running(str(instance.id)):
            JobExecutor().stop_job(str(instance.id))
        instance.delete()

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Start job execution.

        POST /jobs/{id}/start/
        """
        job = self.get_object()

        if not job.enabled:
            return Response(
                {'error': 'Job is disabled'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if JobExecutor().is_running(str(job.id)):
            return Response(
                {'error': 'Job is already running'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prepare job config
        job_config = self._build_job_config(job)

        # Start the job
        success = JobExecutor().start_job(
            job_id=str(job.id),
            job_config=job_config,
            read_callback=self._create_read_callback(job),
            write_callback=self._create_write_callback(job)
        )

        if success:
            job.status = JobStatus.RUNNING
            job.save(update_fields=['status', 'updated_at'])

            # Create job run record
            JobRun.objects.create(
                job=job,
                started_at=timezone.now()
            )

        return Response({
            'ok': success,
            'job_id': str(job.id),
            'status': job.status
        })

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """
        Pause job execution.

        POST /jobs/{id}/pause/
        """
        job = self.get_object()

        success = JobExecutor().pause_job(str(job.id))

        if success:
            job.status = JobStatus.PAUSED
            job.save(update_fields=['status', 'updated_at'])
            self._finalize_job_run(job)

        return Response({
            'ok': success,
            'job_id': str(job.id),
            'status': job.status
        })

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """
        Stop job execution.

        POST /jobs/{id}/stop/
        """
        job = self.get_object()

        success = JobExecutor().stop_job(str(job.id))

        if success:
            job.status = JobStatus.STOPPED
            job.save(update_fields=['status', 'updated_at'])
            self._finalize_job_run(job)

        return Response({
            'ok': success,
            'job_id': str(job.id),
            'status': job.status
        })

    @action(detail=False, methods=['post'])
    def stop_all(self, request):
        """
        Stop all running jobs.

        POST /jobs/stop_all/
        """
        count = JobExecutor().stop_all_jobs()

        # Update all job statuses
        Job.objects.filter(status=JobStatus.RUNNING).update(status=JobStatus.STOPPED)

        return Response({
            'ok': True,
            'stopped_count': count
        })

    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        """
        Get metrics for a job.

        GET /jobs/{id}/metrics/
        """
        job = self.get_object()
        metrics = JobExecutor().get_metrics(str(job.id))

        if metrics:
            return Response(metrics)
        else:
            return Response({
                'job_id': str(job.id),
                'message': 'No metrics available (job may not have run yet)'
            })

    @action(detail=False, methods=['get'], url_path='metrics/summary')
    def metrics_summary(self, request):
        """
        Get metrics summary for all jobs.

        GET /jobs/metrics/summary/
        """
        metrics = JobExecutor().get_all_metrics()

        # Add aggregate stats from database
        db_stats = JobRun.objects.aggregate(
            total_runs=Count('id'),
            total_rows=Sum('rows_written'),
            total_errors=Sum('read_errors') + Sum('write_errors'),
            avg_latency=Avg('avg_latency_ms')
        )

        return Response({
            'live_metrics': metrics,
            'historical': db_stats
        })

    @action(detail=True, methods=['get'])
    def runs(self, request, pk=None):
        """
        Get run history for a job.

        GET /jobs/{id}/runs/
        """
        job = self.get_object()
        runs = job.runs.all()[:50]  # Last 50 runs
        serializer = JobRunSerializer(runs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def dry_run(self, request, pk=None):
        """
        Test job execution without writing data.

        POST /jobs/{id}/dry_run/
        """
        job = self.get_object()
        results = []

        for table in job.tables.all():
            table_result = {
                'table_id': str(table.id),
                'table_name': table.name,
                'values': {},
                'errors': []
            }

            if not table.device:
                table_result['errors'].append('No device bound to table')
                results.append(table_result)
                continue

            for mapping in table.mappings.all():
                try:
                    value = self._read_mapping_value(table.device, mapping)
                    table_result['values'][mapping.field_key] = value
                except Exception as e:
                    table_result['errors'].append(f'{mapping.field_key}: {str(e)}')

            results.append(table_result)

        return Response({
            'job_id': str(job.id),
            'job_name': job.name,
            'tables': results
        })

    def _build_job_config(self, job):
        """Build job configuration dict for executor."""
        triggers = []
        for trigger in job.triggers.all():
            triggers.append({
                'field': trigger.field,
                'operator': trigger.operator,
                'value': trigger.value,
                'deadband': trigger.deadband,
                'cooldown_ms': trigger.cooldown_ms
            })

        return {
            'job_type': job.job_type,
            'interval_ms': job.interval_ms,
            'table_ids': [str(t.id) for t in job.tables.all()],
            'triggers': triggers,
            'batch_size': job.batch_size
        }

    def _create_read_callback(self, job):
        """Create read callback for job executor."""
        # Pre-load table data
        tables = {
            str(t.id): t for t in job.tables.select_related(
                'device', 'device__modbus_config', 'device__opcua_config'
            ).prefetch_related('mappings').all()
        }

        def read_callback(table_id):
            table = tables.get(table_id)
            if not table or not table.device:
                return None

            values = {}
            for mapping in table.mappings.all():
                try:
                    value = self._read_mapping_value(table.device, mapping)
                    values[mapping.field_key] = value
                except Exception:
                    values[mapping.field_key] = None

            return values

        return read_callback

    def _create_write_callback(self, job):
        """Create write callback for job executor."""
        # Pre-load table data
        tables = {
            str(t.id): t for t in job.tables.select_related('storage_target').all()
        }

        def write_callback(table_id, rows):
            table = tables.get(table_id)
            if not table or not table.storage_target:
                return False

            if isinstance(rows, dict):
                rows = [rows]

            success, count, error = StorageService().insert_batch(
                provider=table.storage_target.provider,
                connection_string=table.storage_target.connection_string,
                table_name=table.name,
                rows=rows
            )
            return success

        return write_callback

    def _read_mapping_value(self, device, mapping):
        """Read a single mapping value from the device."""
        if mapping.protocol == 'modbus':
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

    def _finalize_job_run(self, job):
        """Update the latest job run record with final metrics."""
        try:
            run = job.runs.filter(stopped_at__isnull=True).latest('started_at')
            metrics = JobExecutor().get_metrics(str(job.id))

            run.stopped_at = timezone.now()
            if run.started_at:
                run.duration_ms = int((run.stopped_at - run.started_at).total_seconds() * 1000)

            if metrics:
                run.rows_written = metrics.get('rows_written', 0)
                run.reads_count = metrics.get('reads', 0)
                run.read_errors = metrics.get('read_errors', 0)
                run.write_errors = metrics.get('write_errors', 0)
                run.avg_latency_ms = metrics.get('avg_read_latency_ms')
                run.p95_latency_ms = metrics.get('p95_read_latency_ms')
                run.error_log = metrics.get('recent_errors', [])

            run.save()
        except JobRun.DoesNotExist:
            pass
