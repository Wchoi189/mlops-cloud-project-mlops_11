#!/usr/bin/env python3
"""
MLflow server with integrated Prometheus metrics
"""

import mlflow
from mlflow.tracking import MlflowClient
import os
import subprocess
import time
import logging
import threading
from prometheus_client import start_http_server, Gauge, Counter, Info

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
running_experiments = Gauge('mlflow_running_experiments_total', 'Number of MLflow experiments')
total_runs = Gauge('mlflow_runs_total', 'Total number of MLflow runs')
mlflow_info = Info('mlflow_server_info', 'MLflow server information')

def update_metrics():
    """Update Prometheus metrics"""
    try:
        tracking_uri = "sqlite:////mlruns/mlflow.db"
        client = MlflowClient(tracking_uri=tracking_uri)
        
        # Get experiments
        experiments = client.search_experiments()
        experiment_count = len(experiments)
        running_experiments.set(experiment_count)
        
        # Get total runs across all experiments
        total_run_count = 0
        for exp in experiments:
            runs = client.search_runs(experiment_ids=[exp.experiment_id])
            total_run_count += len(runs)
        
        total_runs.set(total_run_count)
        
        # Update server info
        mlflow_info.info({
            'version': mlflow.__version__,
            'backend_store': 'sqlite',
            'artifact_root': '/mlartifacts',
            'host': '0.0.0.0',
            'port': '5000'
        })
        
        logger.info(f"Metrics updated: {experiment_count} experiments, {total_run_count} runs")
        
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
    
    # Start Prometheus metrics server
    try:
        start_http_server(9090)
        logger.info("Prometheus metrics server started on port 9090")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")
    
    # Ensure directories exist
    os.makedirs('/mlruns', exist_ok=True)
    os.makedirs('/mlartifacts', exist_ok=True)
    
    # Check permissions
    if os.access('/mlruns', os.W_OK):
        logger.info("MLruns directory is writable")
    else:
        logger.warning("MLruns directory is not writable")
    
    # Set tracking URI
    tracking_uri = "sqlite:////mlruns/mlflow.db"
    logger.info(f"Setting tracking URI to: {tracking_uri}")
    mlflow.set_tracking_uri(tracking_uri)
    
    # Start metrics collection in background
    metrics_thread = threading.Thread(target=metrics_collector, daemon=True)
    metrics_thread.start()
    logger.info("Background metrics collection started")
    
    # Start MLflow server
    mlflow_cmd = [
        "mlflow", "server",
        "--host", "0.0.0.0",
        "--port", "5000",
        "--backend-store-uri", tracking_uri,
        "--default-artifact-root", "/mlartifacts",
        "--serve-artifacts"
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