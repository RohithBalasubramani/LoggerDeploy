"""
Job Executor Service

Handles job execution threads, scheduling, metrics tracking,
and trigger evaluation for data logging jobs.
"""

import threading
import logging
import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass, field
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class JobMetrics:
    """Metrics for a single job."""
    job_id: str
    reads: int = 0
    read_errors: int = 0
    writes: int = 0
    write_errors: int = 0
    rows_written: int = 0
    triggers_evaluated: int = 0
    triggers_fired: int = 0
    triggers_suppressed: int = 0
    read_latencies: deque = field(default_factory=lambda: deque(maxlen=1000))
    write_latencies: deque = field(default_factory=lambda: deque(maxlen=1000))
    started_at: Optional[datetime] = None
    last_read_at: Optional[datetime] = None
    last_write_at: Optional[datetime] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)

    def record_read(self, latency_ms: float, success: bool = True):
        self.reads += 1
        if success:
            self.read_latencies.append(latency_ms)
            self.last_read_at = datetime.utcnow()
        else:
            self.read_errors += 1

    def record_write(self, latency_ms: float, rows: int = 1, success: bool = True):
        self.writes += 1
        if success:
            self.write_latencies.append(latency_ms)
            self.rows_written += rows
            self.last_write_at = datetime.utcnow()
        else:
            self.write_errors += 1

    def record_trigger(self, fired: bool, suppressed: bool = False):
        self.triggers_evaluated += 1
        if fired:
            self.triggers_fired += 1
        if suppressed:
            self.triggers_suppressed += 1

    def record_error(self, code: str, message: str):
        self.errors.append({
            'code': code,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        })
        # Keep only last 100 errors
        if len(self.errors) > 100:
            self.errors = self.errors[-100:]

    def get_summary(self) -> Dict[str, Any]:
        read_lats = list(self.read_latencies)
        write_lats = list(self.write_latencies)

        return {
            'job_id': self.job_id,
            'reads': self.reads,
            'read_errors': self.read_errors,
            'writes': self.writes,
            'write_errors': self.write_errors,
            'rows_written': self.rows_written,
            'triggers_evaluated': self.triggers_evaluated,
            'triggers_fired': self.triggers_fired,
            'triggers_suppressed': self.triggers_suppressed,
            'avg_read_latency_ms': sum(read_lats) / len(read_lats) if read_lats else None,
            'avg_write_latency_ms': sum(write_lats) / len(write_lats) if write_lats else None,
            'p95_read_latency_ms': sorted(read_lats)[int(len(read_lats) * 0.95)] if len(read_lats) > 20 else None,
            'p95_write_latency_ms': sorted(write_lats)[int(len(write_lats) * 0.95)] if len(write_lats) > 20 else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'last_read_at': self.last_read_at.isoformat() if self.last_read_at else None,
            'last_write_at': self.last_write_at.isoformat() if self.last_write_at else None,
            'recent_errors': self.errors[-10:],
        }

    def reset(self):
        self.reads = 0
        self.read_errors = 0
        self.writes = 0
        self.write_errors = 0
        self.rows_written = 0
        self.triggers_evaluated = 0
        self.triggers_fired = 0
        self.triggers_suppressed = 0
        self.read_latencies.clear()
        self.write_latencies.clear()
        self.started_at = datetime.utcnow()
        self.last_read_at = None
        self.last_write_at = None
        self.errors.clear()


class JobExecutor:
    """
    Singleton service for job execution.

    Manages job threads, scheduling, and metrics collection.
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

        self._job_threads: Dict[str, threading.Thread] = {}
        self._job_stops: Dict[str, threading.Event] = {}
        self._job_metrics: Dict[str, JobMetrics] = {}
        self._job_last_values: Dict[str, Dict[str, Any]] = {}
        self._job_cooldowns: Dict[str, Dict[str, datetime]] = {}
        self._thread_lock = threading.RLock()
        self._initialized = True
        logger.info("JobExecutor initialized")

    def _get_metrics(self, job_id: str) -> JobMetrics:
        """Get or create metrics for a job."""
        if job_id not in self._job_metrics:
            self._job_metrics[job_id] = JobMetrics(job_id=job_id)
        return self._job_metrics[job_id]

    def start_job(
        self,
        job_id: str,
        job_config: Dict[str, Any],
        read_callback: Callable[[str], Dict[str, Any]],
        write_callback: Callable[[str, Dict[str, Any]], bool]
    ) -> bool:
        """
        Start a job execution thread.

        Args:
            job_id: Unique job identifier
            job_config: Job configuration dict
            read_callback: Function to read values for a table (table_id -> values dict)
            write_callback: Function to write values (table_id, values -> success)

        Returns:
            True if job started successfully
        """
        with self._thread_lock:
            if job_id in self._job_threads and self._job_threads[job_id].is_alive():
                logger.warning(f"Job {job_id} is already running")
                return False

            stop_event = threading.Event()
            self._job_stops[job_id] = stop_event

            metrics = self._get_metrics(job_id)
            metrics.reset()

            thread = threading.Thread(
                target=self._run_job_loop,
                args=(job_id, job_config, read_callback, write_callback, stop_event),
                daemon=True,
                name=f"job-{job_id[:8]}"
            )
            self._job_threads[job_id] = thread
            thread.start()

            logger.info(f"Started job {job_id}")
            return True

    def stop_job(self, job_id: str, timeout: float = 5.0) -> bool:
        """
        Stop a running job.

        Args:
            job_id: Job identifier
            timeout: Seconds to wait for thread to stop

        Returns:
            True if job stopped successfully
        """
        with self._thread_lock:
            stop_event = self._job_stops.get(job_id)
            thread = self._job_threads.get(job_id)

            if stop_event is None or thread is None:
                logger.warning(f"Job {job_id} not found")
                return False

            stop_event.set()

        # Wait outside lock
        if thread.is_alive():
            thread.join(timeout=timeout)

        with self._thread_lock:
            self._job_threads.pop(job_id, None)
            self._job_stops.pop(job_id, None)
            self._job_last_values.pop(job_id, None)
            self._job_cooldowns.pop(job_id, None)

        logger.info(f"Stopped job {job_id}")
        return True

    def pause_job(self, job_id: str) -> bool:
        """Pause a job (same as stop, but preserves metrics)."""
        return self.stop_job(job_id)

    def stop_all_jobs(self) -> int:
        """Stop all running jobs. Returns count of jobs stopped."""
        with self._thread_lock:
            job_ids = list(self._job_threads.keys())

        count = 0
        for job_id in job_ids:
            if self.stop_job(job_id):
                count += 1

        return count

    def is_running(self, job_id: str) -> bool:
        """Check if a job is running."""
        with self._thread_lock:
            thread = self._job_threads.get(job_id)
            return thread is not None and thread.is_alive()

    def get_metrics(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics summary for a job."""
        metrics = self._job_metrics.get(job_id)
        if metrics:
            return metrics.get_summary()
        return None

    def get_all_metrics(self) -> List[Dict[str, Any]]:
        """Get metrics for all jobs."""
        return [m.get_summary() for m in self._job_metrics.values()]

    def _run_job_loop(
        self,
        job_id: str,
        job_config: Dict[str, Any],
        read_callback: Callable,
        write_callback: Callable,
        stop_event: threading.Event
    ):
        """Main job execution loop."""
        job_type = job_config.get('job_type', 'continuous')
        interval_ms = job_config.get('interval_ms', 1000)
        table_ids = job_config.get('table_ids', [])
        triggers = job_config.get('triggers', [])
        batch_size = job_config.get('batch_size', 1)

        metrics = self._get_metrics(job_id)
        interval_sec = interval_ms / 1000.0

        # Initialize last values for trigger jobs
        if job_type == 'trigger':
            self._job_last_values[job_id] = {}
            self._job_cooldowns[job_id] = {}

        batch_buffer: Dict[str, List[Dict[str, Any]]] = {tid: [] for tid in table_ids}

        logger.info(f"Job {job_id} loop started (type={job_type}, interval={interval_ms}ms)")

        while not stop_event.is_set():
            loop_start = time.perf_counter()

            for table_id in table_ids:
                try:
                    # Read values
                    read_start = time.perf_counter()
                    values = read_callback(table_id)
                    read_latency = (time.perf_counter() - read_start) * 1000
                    metrics.record_read(read_latency, success=True)

                    if values is None:
                        continue

                    # Handle based on job type
                    if job_type == 'continuous':
                        should_write = True
                    else:  # trigger
                        should_write = self._evaluate_triggers(
                            job_id, table_id, values, triggers, metrics
                        )

                    if should_write:
                        # Add to batch buffer
                        values['timestamp_utc'] = datetime.utcnow()
                        batch_buffer[table_id].append(values)

                        # Write if batch is full
                        if len(batch_buffer[table_id]) >= batch_size:
                            write_start = time.perf_counter()
                            success = write_callback(table_id, batch_buffer[table_id])
                            write_latency = (time.perf_counter() - write_start) * 1000
                            metrics.record_write(
                                write_latency,
                                rows=len(batch_buffer[table_id]),
                                success=success
                            )
                            batch_buffer[table_id] = []

                except Exception as e:
                    logger.error(f"Job {job_id} error for table {table_id}: {e}")
                    metrics.record_error('LOOP_ERROR', str(e))
                    metrics.record_read(0, success=False)

            # Sleep for remaining interval
            elapsed = time.perf_counter() - loop_start
            sleep_time = max(0, interval_sec - elapsed)
            if sleep_time > 0:
                stop_event.wait(sleep_time)

        # Flush remaining batches on stop
        for table_id, buffer in batch_buffer.items():
            if buffer:
                try:
                    write_callback(table_id, buffer)
                except Exception as e:
                    logger.error(f"Job {job_id} flush error: {e}")

        logger.info(f"Job {job_id} loop ended")

    def _evaluate_triggers(
        self,
        job_id: str,
        table_id: str,
        values: Dict[str, Any],
        triggers: List[Dict[str, Any]],
        metrics: JobMetrics
    ) -> bool:
        """
        Evaluate trigger conditions.

        Returns True if any trigger fires and cooldown has expired.
        """
        last_values = self._job_last_values.get(job_id, {}).get(table_id, {})
        cooldowns = self._job_cooldowns.get(job_id, {})
        now = datetime.utcnow()

        any_fired = False

        for trigger in triggers:
            field = trigger.get('field')
            operator = trigger.get('operator', 'change')
            threshold = trigger.get('value')
            deadband = trigger.get('deadband', 0)
            cooldown_ms = trigger.get('cooldown_ms', 0)

            if field not in values:
                continue

            new_val = values[field]
            old_val = last_values.get(field)

            fired = False

            if operator == 'change':
                if old_val is not None:
                    diff = abs(new_val - old_val) if isinstance(new_val, (int, float)) else (new_val != old_val)
                    fired = diff > deadband if isinstance(diff, (int, float)) else diff

            elif operator == 'rising':
                if old_val is not None and threshold is not None:
                    fired = old_val <= threshold and new_val > threshold

            elif operator == 'falling':
                if old_val is not None and threshold is not None:
                    fired = old_val >= threshold and new_val < threshold

            elif operator == '>':
                fired = new_val > threshold if threshold is not None else False

            elif operator == '>=':
                fired = new_val >= threshold if threshold is not None else False

            elif operator == '<':
                fired = new_val < threshold if threshold is not None else False

            elif operator == '<=':
                fired = new_val <= threshold if threshold is not None else False

            elif operator == '==':
                fired = new_val == threshold if threshold is not None else False

            elif operator == '!=':
                fired = new_val != threshold if threshold is not None else False

            # Check cooldown
            cooldown_key = f"{table_id}:{field}"
            if fired and cooldown_ms > 0:
                last_fire = cooldowns.get(cooldown_key)
                if last_fire:
                    elapsed_ms = (now - last_fire).total_seconds() * 1000
                    if elapsed_ms < cooldown_ms:
                        metrics.record_trigger(fired=True, suppressed=True)
                        fired = False  # Suppressed by cooldown

            if fired:
                cooldowns[cooldown_key] = now
                any_fired = True
                metrics.record_trigger(fired=True, suppressed=False)
            else:
                metrics.record_trigger(fired=False, suppressed=False)

        # Update last values
        if job_id not in self._job_last_values:
            self._job_last_values[job_id] = {}
        self._job_last_values[job_id][table_id] = values.copy()

        return any_fired


# Singleton instance
job_executor = JobExecutor()
