"""
Monitoring Module

Provides utilities for agent observability, metrics, and logging.
"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional
from google.cloud import monitoring_v3, logging as cloud_logging
import json

logger = logging.getLogger(__name__)


class AgentMonitoring:
    """Monitoring and observability for agents"""
    
    def __init__(self, project_id: str, agent_name: str):
        """
        Initialize monitoring
        
        Args:
            project_id: GCP project ID
            agent_name: Name of the agent
        """
        self.project_id = project_id
        self.agent_name = agent_name
        self.metrics_client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{project_id}"
        
        # Initialize structured logging
        self.logging_client = cloud_logging.Client(project=project_id)
        self.logging_client.setup_logging()
    
    def track_invocation(self):
        """Decorator to track agent invocations"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                success = False
                error = None
                
                try:
                    result = func(*args, **kwargs)
                    success = True
                    return result
                    
                except Exception as e:
                    error = str(e)
                    logger.error(f"Agent invocation failed: {e}")
                    raise
                    
                finally:
                    duration = time.time() - start_time
                    
                    # Log invocation
                    self._log_invocation(
                        duration=duration,
                        success=success,
                        error=error,
                        input_data=args[1] if len(args) > 1 else kwargs.get('input_data')
                    )
                    
                    # Send metrics
                    self._send_invocation_metrics(duration, success)
            
            return wrapper
        return decorator
    
    def _log_invocation(
        self,
        duration: float,
        success: bool,
        error: Optional[str] = None,
        input_data: Optional[Dict] = None
    ):
        """Log agent invocation"""
        log_entry = {
            "agent": self.agent_name,
            "duration_seconds": duration,
            "success": success,
            "timestamp": time.time(),
        }
        
        if error:
            log_entry["error"] = error
        
        if input_data:
            # Log sanitized input (remove sensitive data)
            log_entry["input_size"] = len(str(input_data))
        
        logger.info(json.dumps(log_entry))
    
    def _send_invocation_metrics(self, duration: float, success: bool):
        """Send metrics to Cloud Monitoring"""
        try:
            # Create time series for invocation count
            self._write_time_series(
                metric_type="custom.googleapis.com/agent/invocations",
                value=1,
                labels={"agent": self.agent_name, "success": str(success)}
            )
            
            # Create time series for duration
            self._write_time_series(
                metric_type="custom.googleapis.com/agent/duration",
                value=duration,
                labels={"agent": self.agent_name}
            )
            
        except Exception as e:
            logger.warning(f"Failed to send metrics: {e}")
    
    def _write_time_series(
        self,
        metric_type: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """Write a time series to Cloud Monitoring"""
        series = monitoring_v3.TimeSeries()
        series.metric.type = metric_type
        
        if labels:
            for key, val in labels.items():
                series.metric.labels[key] = val
        
        series.resource.type = "global"
        
        now = time.time()
        seconds = int(now)
        nanos = int((now - seconds) * 10 ** 9)
        
        interval = monitoring_v3.TimeInterval(
            {"end_time": {"seconds": seconds, "nanos": nanos}}
        )
        
        point = monitoring_v3.Point(
            {"interval": interval, "value": {"double_value": value}}
        )
        
        series.points = [point]
        
        self.metrics_client.create_time_series(
            name=self.project_name,
            time_series=[series]
        )


class MetricsCollector:
    """Collect custom metrics from agents"""
    
    def __init__(self, project_id: str, agent_name: str):
        """
        Initialize metrics collector
        
        Args:
            project_id: GCP project ID
            agent_name: Name of the agent
        """
        self.project_id = project_id
        self.agent_name = agent_name
        self.client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{project_id}"
    
    def record_metric(
        self,
        metric_name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Record a custom metric
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            labels: Optional labels for the metric
        """
        metric_type = f"custom.googleapis.com/agent/{metric_name}"
        
        series = monitoring_v3.TimeSeries()
        series.metric.type = metric_type
        series.metric.labels["agent"] = self.agent_name
        
        if labels:
            for key, val in labels.items():
                series.metric.labels[key] = val
        
        series.resource.type = "global"
        
        now = time.time()
        seconds = int(now)
        nanos = int((now - seconds) * 10 ** 9)
        
        interval = monitoring_v3.TimeInterval(
            {"end_time": {"seconds": seconds, "nanos": nanos}}
        )
        
        point = monitoring_v3.Point(
            {"interval": interval, "value": {"double_value": value}}
        )
        
        series.points = [point]
        
        try:
            self.client.create_time_series(
                name=self.project_name,
                time_series=[series]
            )
            logger.debug(f"Recorded metric: {metric_name}={value}")
        except Exception as e:
            logger.warning(f"Failed to record metric {metric_name}: {e}")
    
    def increment_counter(
        self,
        counter_name: str,
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Increment a counter metric
        
        Args:
            counter_name: Name of the counter
            labels: Optional labels
        """
        self.record_metric(counter_name, 1, labels)
    
    def record_histogram(
        self,
        histogram_name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Record a histogram value
        
        Args:
            histogram_name: Name of the histogram
            value: Value to record
            labels: Optional labels
        """
        self.record_metric(f"{histogram_name}_histogram", value, labels)


class PerformanceTracker:
    """Track agent performance metrics"""
    
    def __init__(self, agent_name: str):
        """
        Initialize performance tracker
        
        Args:
            agent_name: Name of the agent
        """
        self.agent_name = agent_name
        self._start_times = {}
    
    def start_span(self, span_name: str):
        """Start a performance span"""
        self._start_times[span_name] = time.time()
    
    def end_span(self, span_name: str) -> float:
        """
        End a performance span
        
        Args:
            span_name: Name of the span
            
        Returns:
            Duration in seconds
        """
        if span_name not in self._start_times:
            logger.warning(f"Span {span_name} was not started")
            return 0.0
        
        duration = time.time() - self._start_times[span_name]
        del self._start_times[span_name]
        
        logger.debug(f"Span {span_name} took {duration:.3f}s")
        return duration
    
    def measure_execution_time(self):
        """Decorator to measure function execution time"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                span_name = func.__name__
                self.start_span(span_name)
                
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = self.end_span(span_name)
                    logger.info(f"{self.agent_name}.{span_name} executed in {duration:.3f}s")
            
            return wrapper
        return decorator
