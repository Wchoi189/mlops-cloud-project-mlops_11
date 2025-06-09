"""
MLOps Prometheus Metrics Collection
Custom metrics for API, models, and data monitoring
"""

import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Optional, Union

import numpy as np

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        Info,
        Summary,
        generate_latest,
        multiprocess,
        start_http_server,
    )

    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False

    # Fallback classes for when prometheus_client is not available
    class DummyMetric:
        def __init__(self, *args, **kwargs):
            pass

        def inc(self, *args, **kwargs):
            pass

        def dec(self, *args, **kwargs):
            pass

        def set(self, *args, **kwargs):
            pass

        def observe(self, *args, **kwargs):
            pass

        def info(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs):
            return self

        def time(self):
            return self

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    Counter = Histogram = Gauge = Summary = Info = DummyMetric

import logging

logger = logging.getLogger(__name__)


class MLOpsMetrics:
    """Centralized metrics collection for MLOps pipeline"""

    def __init__(
        self, enabled: bool = True, registry: Optional[CollectorRegistry] = None
    ):
        self.registry = registry
        self.enabled = enabled

        if not self.enabled:
            logger.warning("Prometheus client not available. Metrics will be disabled.")
            return

        # API Performance Metrics
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status_code"],
            registry=registry,
        )

        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=registry,
        )

        # Model Performance Metrics
        self.model_prediction_duration_seconds = Histogram(
            "model_prediction_duration_seconds",
            "Model prediction duration in seconds",
            ["model_name", "model_version"],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
            registry=registry,
        )

        self.model_predictions_total = Counter(
            "model_predictions_total",
            "Total model predictions",
            ["model_name", "model_version", "prediction_type"],
            registry=registry,
        )

        self.model_accuracy_score = Gauge(
            "model_accuracy_score",
            "Current model accuracy score",
            ["model_name", "model_version"],
            registry=registry,
        )

        self.model_training_duration_seconds = Histogram(
            "model_training_duration_seconds",
            "Model training duration in seconds",
            ["model_name", "training_type"],
            buckets=[60, 300, 600, 1800, 3600, 7200, 14400],
            registry=registry,
        )

        self.model_training_failures_total = Counter(
            "model_training_failures_total",
            "Total model training failures",
            ["model_name", "error_type"],
            registry=registry,
        )

        # Data Quality Metrics
        self.data_drift_score = Gauge(
            "data_drift_score",
            "Data drift detection score",
            ["feature_name", "model_name"],
            registry=registry,
        )

        self.data_validation_errors_total = Counter(
            "data_validation_errors_total",
            "Total data validation errors",
            ["validation_type", "error_type"],
            registry=registry,
        )

        self.data_processing_duration_seconds = Histogram(
            "data_processing_duration_seconds",
            "Data processing duration in seconds",
            ["processing_step"],
            buckets=[1, 5, 10, 30, 60, 300, 600],
            registry=registry,
        )

        # System Resource Metrics
        self.memory_usage_bytes = Gauge(
            "mlops_memory_usage_bytes",
            "Memory usage in bytes",
            ["component"],
            registry=registry,
        )

        self.cpu_usage_percent = Gauge(
            "mlops_cpu_usage_percent",
            "CPU usage percentage",
            ["component"],
            registry=registry,
        )

        # MLflow Integration Metrics
        self.mlflow_experiments_total = Counter(
            "mlflow_experiments_total",
            "Total MLflow experiments",
            ["experiment_name"],
            registry=registry,
        )

        self.mlflow_runs_total = Counter(
            "mlflow_runs_total",
            "Total MLflow runs",
            ["experiment_name", "status"],
            registry=registry,
        )

        # Business Metrics
        self.prediction_ratings_distribution = Histogram(
            "prediction_ratings_distribution",
            "Distribution of predicted ratings",
            ["rating_range"],
            buckets=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            registry=registry,
        )

        self.api_users_active = Gauge(
            "api_users_active", "Number of active API users", registry=registry
        )

        # Application Info
        self.app_info = Info(
            "mlops_app_info", "Application information", registry=registry
        )

        # Set application info
        self.set_app_info()

        logger.info("MLOps metrics initialized successfully")

    def set_app_info(self):
        """Set application information metrics"""
        if not self.enabled:
            return

        try:
            import platform
            import sys

            self.app_info.info(
                {
                    "version": "1.0.0",
                    "python_version": sys.version.split()[0],
                    "platform": platform.system(),
                    "component": "mlops-imdb-api",
                }
            )
        except Exception as e:
            logger.warning(f"Failed to set app info: {e}")

    # Decorator methods for automatic metrics collection
    def track_requests(self, endpoint: str):
        """Decorator to track HTTP requests"""

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not self.enabled:
                    return await func(*args, **kwargs)

                start_time = time.time()
                status_code = 200

                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    status_code = 500
                    raise
                finally:
                    duration = time.time() - start_time

                    # Get method from request if available
                    method = getattr(args[0], "method", "GET") if args else "GET"

                    self.http_requests_total.labels(
                        method=method, endpoint=endpoint, status_code=str(status_code)
                    ).inc()

                    self.http_request_duration_seconds.labels(
                        method=method, endpoint=endpoint
                    ).observe(duration)

            return wrapper

        return decorator

    def track_predictions(self, model_name: str, model_version: str = "1.0"):
        """Decorator to track model predictions"""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)

                start_time = time.time()
                prediction_type = "single"

                try:
                    result = func(*args, **kwargs)

                    # Determine prediction type based on result
                    if isinstance(result, (list, np.ndarray)):
                        prediction_type = "batch"

                    return result

                except Exception as e:
                    prediction_type = "failed"
                    raise
                finally:
                    duration = time.time() - start_time

                    self.model_prediction_duration_seconds.labels(
                        model_name=model_name, model_version=model_version
                    ).observe(duration)

                    self.model_predictions_total.labels(
                        model_name=model_name,
                        model_version=model_version,
                        prediction_type=prediction_type,
                    ).inc()

            return wrapper

        return decorator

    def track_training(self, model_name: str, training_type: str = "full"):
        """Decorator to track model training"""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)

                start_time = time.time()

                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    # Track training failure
                    error_type = type(e).__name__
                    self.model_training_failures_total.labels(
                        model_name=model_name, error_type=error_type
                    ).inc()
                    raise
                finally:
                    duration = time.time() - start_time
                    self.model_training_duration_seconds.labels(
                        model_name=model_name, training_type=training_type
                    ).observe(duration)

            return wrapper

        return decorator

    # Manual metric recording methods
    def record_prediction_rating(self, rating: float):
        """Record a prediction rating for distribution analysis"""
        if not self.enabled:
            return

        # Determine rating range
        rating_range = f"{int(rating)}-{int(rating)+1}"

        self.prediction_ratings_distribution.labels(rating_range=rating_range).observe(
            rating
        )

    def record_data_drift(
        self, feature_name: str, drift_score: float, model_name: str = "default"
    ):
        """Record data drift score"""
        if not self.enabled:
            return

        self.data_drift_score.labels(
            feature_name=feature_name, model_name=model_name
        ).set(drift_score)

    def record_model_accuracy(
        self, accuracy: float, model_name: str = "default", model_version: str = "1.0"
    ):
        """Record model accuracy score"""
        if not self.enabled:
            return

        self.model_accuracy_score.labels(
            model_name=model_name, model_version=model_version
        ).set(accuracy)

    def record_resource_usage(
        self, component: str, memory_bytes: int, cpu_percent: float
    ):
        """Record resource usage"""
        if not self.enabled:
            return

        self.memory_usage_bytes.labels(component=component).set(memory_bytes)
        self.cpu_usage_percent.labels(component=component).set(cpu_percent)

    def record_mlflow_experiment(self, experiment_name: str, status: str = "completed"):
        """Record MLflow experiment"""
        if not self.enabled:
            return

        self.mlflow_experiments_total.labels(experiment_name=experiment_name).inc()

        self.mlflow_runs_total.labels(
            experiment_name=experiment_name, status=status
        ).inc()

    def set_active_users(self, count: int):
        """Set number of active users"""
        if not self.enabled:
            return

        self.api_users_active.set(count)

    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format"""
        if not self.enabled:
            return "# Metrics not available\n"

        try:
            if self.registry:
                metrics_bytes = generate_latest(self.registry)
            else:
                metrics_bytes = generate_latest()

            # 일관성 있는 API를 위해서 bytes 에서 str 으로 해독하기기
            return metrics_bytes.decode("utf-8")

        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            return f"# Error generating metrics: {e}\n"


# Global metrics instance
metrics = MLOpsMetrics()

# # Context managers for timing operations
# class MetricsTimer:
#     """Context manager for timing operations"""

#     def __init__(self, metric_func, *labels):
#         self.metric_func = metric_func
#         self.labels = labels
#         self.start_time = None

#     def __enter__(self):
#         self.start_time = time.time()
#         return self

#     def __exit__(self, exc_type, exc_val, exc_tb):
#         if self.start_time and metrics.enabled:
#             duration = time.time() - self.start_time
#             self.metric_func(*self.labels).observe(duration)

# # Utility functions for easy metrics collection
# def track_api_call(endpoint: str, method: str = "GET"):
#     """Context manager to track API calls"""
#     return MetricsTimer(
#         lambda e, m: metrics.http_request_duration_seconds.labels(endpoint=e, method=m),
#         endpoint, method
#     )


# def track_prediction_time(model_name: str = "imdb_model", model_version: str = "1.0"):
#     """Context manager to track prediction time"""
#     return MetricsTimer(
#         lambda mn, mv: metrics.model_prediction_duration_seconds.labels(model_name=mn, model_version=mv),
#         model_name, model_version
#     )
# Context manager for timing
class MetricsTimer:
    def __init__(self, metric_func, *args, **kwargs):
        self.metric_func = metric_func
        self.args = args
        self.kwargs = kwargs
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            try:
                metric = self.metric_func(*self.args, **self.kwargs)
                metric.observe(duration)
            except Exception as e:
                logger.error(f"Failed to record metric: {e}")


# Decorator functions
def track_prediction_time(model_name: str = "imdb_model", model_version: str = "1.0"):
    """Decorator to track prediction time"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # Record the metric
                try:
                    metrics.model_prediction_duration_seconds.labels(
                        model_name=model_name, model_version=model_version
                    ).observe(duration)
                except Exception as e:
                    logger.error(f"Failed to record prediction time: {e}")

                return result
            except Exception as e:
                duration = time.time() - start_time
                # Record failed prediction time too
                try:
                    metrics.model_prediction_duration_seconds.labels(
                        model_name=model_name, model_version=model_version
                    ).observe(duration)
                except:
                    pass
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Record the metric
                try:
                    metrics.model_prediction_duration_seconds.labels(
                        model_name=model_name, model_version=model_version
                    ).observe(duration)
                except Exception as e:
                    logger.error(f"Failed to record prediction time: {e}")

                return result
            except Exception as e:
                duration = time.time() - start_time
                # Record failed prediction time too
                try:
                    metrics.model_prediction_duration_seconds.labels(
                        model_name=model_name, model_version=model_version
                    ).observe(duration)
                except:
                    pass
                raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def track_api_call(endpoint: str, method: str = "GET"):
    """Decorator to track API calls"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = "200"  # Default

            try:
                result = await func(*args, **kwargs)

                # Try to extract status code from response
                if hasattr(result, "status_code"):
                    status_code = str(result.status_code)

                return result

            except Exception as e:
                status_code = "500"
                raise
            finally:
                duration = time.time() - start_time

                # Record metrics
                try:
                    metrics.http_requests_total.labels(
                        method=method, endpoint=endpoint, status_code=status_code
                    ).inc()

                    metrics.http_request_duration_seconds.labels(
                        endpoint=endpoint, method=method
                    ).observe(duration)
                except Exception as e:
                    logger.error(f"Failed to record API call metrics: {e}")

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = "200"  # Default

            try:
                result = func(*args, **kwargs)

                # Try to extract status code from response
                if hasattr(result, "status_code"):
                    status_code = str(result.status_code)

                return result

            except Exception as e:
                status_code = "500"
                raise
            finally:
                duration = time.time() - start_time

                # Record metrics
                try:
                    metrics.http_requests_total.labels(
                        method=method, endpoint=endpoint, status_code=status_code
                    ).inc()

                    metrics.http_request_duration_seconds.labels(
                        endpoint=endpoint, method=method
                    ).observe(duration)
                except Exception as e:
                    logger.error(f"Failed to record API call metrics: {e}")

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def track_data_processing(step: str):
    """Context manager to track data processing time"""
    return MetricsTimer(
        lambda s: metrics.data_processing_duration_seconds.labels(processing_step=s),
        step,
    )


# Middleware for automatic request tracking
class PrometheusMiddleware:
    """FastAPI middleware for automatic metrics collection"""

    def __init__(self, app, metrics_instance: MLOpsMetrics):
        self.app = app
        self.metrics = metrics_instance

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not self.metrics.enabled:
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        status_code = 200

        async def wrapped_send(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)
        except Exception as e:
            status_code = 500
            raise
        finally:
            # Record metrics
            duration = time.time() - start_time
            method = scope["method"]
            path = scope["path"]

            self.metrics.http_requests_total.labels(
                method=method, endpoint=path, status_code=str(status_code)
            ).inc()

            self.metrics.http_request_duration_seconds.labels(
                method=method, endpoint=path
            ).observe(duration)


# Health check metrics
def update_health_metrics():
    """Update system health metrics"""
    if not metrics.enabled:
        return

    try:
        import os

        import psutil

        # Get current process
        process = psutil.Process(os.getpid())

        # Memory usage
        memory_info = process.memory_info()
        metrics.record_resource_usage(
            component="api",
            memory_bytes=memory_info.rss,
            cpu_percent=process.cpu_percent(),
        )

        # System-wide metrics
        system_memory = psutil.virtual_memory()
        system_cpu = psutil.cpu_percent(interval=1)

        metrics.record_resource_usage(
            component="system", memory_bytes=system_memory.used, cpu_percent=system_cpu
        )

    except ImportError:
        logger.warning("psutil not available for system metrics")
    except Exception as e:
        logger.error(f"Error updating health metrics: {e}")


# Background metrics collection
import asyncio
import threading


class MetricsCollector:
    """Background metrics collector"""

    def __init__(self, interval: int = 30):
        self.interval = interval
        self.running = False
        self.thread = None

    def start(self):
        """Start background metrics collection"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._collect_loop, daemon=True)
        self.thread.start()
        logger.info("Background metrics collection started")

    def stop(self):
        """Stop background metrics collection"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Background metrics collection stopped")

    def _collect_loop(self):
        """Main collection loop"""
        while self.running:
            try:
                update_health_metrics()
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                time.sleep(self.interval)


# Create global metrics collector
metrics_collector = MetricsCollector()

# Export functions for easy use
__all__ = [
    "MLOpsMetrics",
    "metrics",
    "track_api_call",
    "track_prediction_time",
    "track_data_processing",
    "PrometheusMiddleware",
    "MetricsCollector",
    "metrics_collector",
    "update_health_metrics",
]
