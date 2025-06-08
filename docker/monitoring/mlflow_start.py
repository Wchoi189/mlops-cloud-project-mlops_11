#!/usr/bin/env python3
"""
MLflow server with integrated Prometheus metrics
"""

import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import mlflow
from mlflow.tracking import MlflowClient
from prometheus_client import Counter, Gauge, Info, start_http_server

# Prometheus imports
try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
        multiprocess,
        start_http_server,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    print("⚠️ Prometheus client not available, metrics disabled")
    PROMETHEUS_AVAILABLE = False

# MLflow imports
try:
    import mlflow
    from mlflow.tracking import MlflowClient

    MLFLOW_AVAILABLE = True
except ImportError:
    print("❌ MLflow not available")
    MLFLOW_AVAILABLE = False
    sys.exit(1)


# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Prometheus metrics - Initialize only if Prometheus is available
MLFLOW_RUNNING_EXPERIMENTS = None
MLFLOW_TOTAL_RUNS = None
MLFLOW_SERVER_INFO = None
MLFLOW_REGISTERED_MODELS = None
MLFLOW_ARTIFACTS_COUNT = None
MLFLOW_API_CALLS = None


def initialize_metrics():
    """Initialize Prometheus metrics safely"""
    global MLFLOW_RUNNING_EXPERIMENTS, MLFLOW_TOTAL_RUNS, MLFLOW_SERVER_INFO
    global MLFLOW_REGISTERED_MODELS, MLFLOW_ARTIFACTS_COUNT, MLFLOW_API_CALLS

    if not PROMETHEUS_AVAILABLE:
        logger.warning("Prometheus not available, metrics disabled")
        return False

    try:
        # Ensure prometheus multiproc directory exists
        prometheus_dir = os.environ.get(
            "PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc"
        )
        Path(prometheus_dir).mkdir(parents=True, exist_ok=True)

        # Clear any existing metric files
        for file in Path(prometheus_dir).glob("*.db"):
            try:
                file.unlink()
            except:
                pass

        # Initialize metrics
        MLFLOW_RUNNING_EXPERIMENTS = Gauge(
            "mlflow_running_experiments_total", "Number of MLflow experiments"
        )
        MLFLOW_TOTAL_RUNS = Gauge("mlflow_runs_total", "Total number of MLflow runs")
        MLFLOW_SERVER_INFO = Info("mlflow_server_info", "MLflow server information")
        MLFLOW_REGISTERED_MODELS = Gauge(
            "mlflow_registered_models", "Total number of registered models"
        )
        MLFLOW_ARTIFACTS_COUNT = Gauge(
            "mlflow_artifacts_total", "Total number of artifacts stored"
        )
        MLFLOW_API_CALLS = Counter(
            "mlflow_api_calls_total", "Total number of MLflow API calls", ["endpoint"]
        )

        logger.info("✅ Prometheus metrics initialized successfully")
        return True

    except Exception as e:
        logger.error(f"⚠️ Failed to initialize Prometheus metrics: {e}")
        return False


def update_metrics():
    """Update Prometheus metrics"""
    if not PROMETHEUS_AVAILABLE or not MLFLOW_RUNNING_EXPERIMENTS:
        return

    try:
        tracking_uri = os.environ.get(
            "MLFLOW_BACKEND_STORE_URI", "sqlite:////mlruns/mlflow.db"
        )
        client = MlflowClient(tracking_uri=tracking_uri)

        # Get experiments
        experiments = client.search_experiments()
        experiment_count = len(experiments)
        MLFLOW_RUNNING_EXPERIMENTS.set(experiment_count)

        # Get registered models
        try:
            registered_models = client.search_registered_models()
            if MLFLOW_REGISTERED_MODELS is not None:
                MLFLOW_REGISTERED_MODELS.set(len(registered_models))
        except Exception as e:
            logger.warning(f"Failed to get registered models: {e}")
            if MLFLOW_REGISTERED_MODELS is not None:
                MLFLOW_REGISTERED_MODELS.set(0)

        # Get total runs across all experiments
        total_run_count = 0
        for exp in experiments:
            runs = client.search_runs(experiment_ids=[exp.experiment_id])
            total_run_count += len(runs)

        if MLFLOW_TOTAL_RUNS is not None:
            MLFLOW_TOTAL_RUNS.set(total_run_count)

        # Count artifacts (simplified approach)
        try:
            artifact_root = os.environ.get(
                "MLFLOW_DEFAULT_ARTIFACT_ROOT", "/mlartifacts"
            )
            if os.path.exists(artifact_root):
                artifact_count = sum(
                    [len(files) for _, _, files in os.walk(artifact_root)]
                )
                if MLFLOW_ARTIFACTS_COUNT is not None:
                    MLFLOW_ARTIFACTS_COUNT.set(artifact_count)
            else:
                if MLFLOW_ARTIFACTS_COUNT is not None:
                    MLFLOW_ARTIFACTS_COUNT.set(0)
        except Exception as e:
            logger.warning(f"Failed to count artifacts: {e}")
            if MLFLOW_ARTIFACTS_COUNT is not None:
                MLFLOW_ARTIFACTS_COUNT.set(0)

        # Update server info
        if MLFLOW_SERVER_INFO is not None:
            MLFLOW_SERVER_INFO.info(
                {
                    "version": mlflow.__version__,
                    "backend_store": os.environ.get(
                        "MLFLOW_BACKEND_STORE_URI", "sqlite:////mlruns/mlflow.db"
                    ),
                    "artifact_root": os.environ.get(
                        "MLFLOW_DEFAULT_ARTIFACT_ROOT", "/mlartifacts"
                    ),
                    "host": "0.0.0.0",
                    "port": "5000",
                }
            )

        logger.info(
            f"Metrics updated: {experiment_count} experiments, {total_run_count} runs"
        )

    except Exception as e:
        logger.error(f"Failed to update metrics: {e}")


def metrics_collector():
    """Background thread for metrics collection"""
    while True:
        try:
            update_metrics()
            time.sleep(30)  # Update every 30 seconds
        except Exception as e:
            logger.error(f"Metrics collection error: {e}")
            time.sleep(30)


def main():
    """Main function"""
    logger.info("Starting MLflow server with Prometheus metrics...")

    # Initialize Prometheus metrics
    metrics_initialized = initialize_metrics()

    # Start Prometheus metrics server only if metrics are available
    if metrics_initialized:
        try:
            # Use port 9090 inside the container (mapped to 9091 on host)
            start_http_server(9090)
            logger.info("Prometheus metrics server started on port 9090")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")

    # Create directories with proper permissions
    for directory in ["/mlruns", "/mlartifacts", "/tmp/prometheus_multiproc"]:
        os.makedirs(directory, exist_ok=True)
        os.chmod(directory, 0o777)  # Full permissions
        logger.info(f"Ensured directory exists with proper permissions: {directory}")
    # Check permissions
    if os.access("/mlruns", os.W_OK):
        logger.info("MLruns directory is writable")
    else:
        logger.warning("MLruns directory is not writable")

    # Set tracking URI from environment or default
    tracking_uri = os.environ.get(
        "MLFLOW_BACKEND_STORE_URI", "sqlite:////mlruns/mlflow.db"
    )
    artifact_root = os.environ.get("MLFLOW_DEFAULT_ARTIFACT_ROOT", "/mlartifacts")

    # Ensure proper SQLite URI format
    if tracking_uri.startswith("sqlite:///") and not tracking_uri.startswith(
        "sqlite:////"
    ):
        tracking_uri = tracking_uri.replace("sqlite:///", "sqlite:////", 1)
        logger.info(f"Adjusted tracking URI format to: {tracking_uri}")

    # Test database access
    try:
        db_file = tracking_uri.replace("sqlite:////", "/")
        db_dir = os.path.dirname(db_file)
        os.makedirs(db_dir, exist_ok=True)  # Ensure directory exists

        with open(db_file, "a"):  # Try to open for append (creates if doesn't exist)
            pass
        logger.info(f"Successfully verified database file access: {db_file}")
    except Exception as e:
        logger.error(f"Cannot access database file: {e}")

    logger.info(f"Setting tracking URI to: {tracking_uri}")
    logger.info(f"Setting artifact root to: {artifact_root}")

    mlflow.set_tracking_uri(tracking_uri)

    # Start metrics collection in background
    metrics_thread = threading.Thread(target=metrics_collector, daemon=True)
    metrics_thread.start()
    logger.info("Background metrics collection started")

    # Start MLflow server
    mlflow_cmd = [
        "mlflow",
        "server",
        "--host",
        "0.0.0.0",
        "--port",
        "5000",
        "--backend-store-uri",
        tracking_uri,
        "--default-artifact-root",
        artifact_root,
        "--serve-artifacts",
    ]

    logger.info(f"Starting MLflow server: {' '.join(mlflow_cmd)}")

    try:
        # Run MLflow server (this blocks)
        subprocess.run(mlflow_cmd, check=True)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except subprocess.CalledProcessError as e:
        logger.error(f"MLflow server failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
