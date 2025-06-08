"""
Enhanced trainer with icecream, tqdm, and rich integration
Better debugging, progress tracking, and visual feedback
"""

import logging
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore")

# Enhanced utilities
from ..utils.enhanced import (
    HAS_ICECREAM,
    HAS_RICH,
    HAS_TQDM,
    EnhancedLogger,
    ProgressTracker,
    display_table,
    enhanced_print,
    ic,
    tools,
)


class EnhancedMovieRatingTrainer:
    """
    Enhanced version of MovieRatingTrainer with better UX
    Features: progress bars, better debugging, rich output
    """

    # Core features (same as original)
    BASE_FEATURES = ["startYear", "runtimeMinutes", "numVotes"]
    TARGET_COLUMN = "averageRating"

    def __init__(self, experiment_name: str = "enhanced_imdb_movie_rating"):
        self.experiment_name = experiment_name
        self.model = None
        self.scaler = None
        self.feature_names = []
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)

        # Enhanced components
        self.logger = EnhancedLogger("EnhancedTrainer")
        self.progress = ProgressTracker()

        # MLflow setup with enhanced logging
        try:
            mlflow.set_experiment(self.experiment_name)
            self.logger.success(f"MLflow experiment setup: {self.experiment_name}")
        except Exception as e:
            self.logger.error(f"MLflow setup failed: {e}")
            ic(e)

    def load_data(
        self, data_path: str = "data/processed/movies_with_ratings.csv"
    ) -> pd.DataFrame:
        """Load data with enhanced progress tracking"""
        self.logger.info("Loading movie data...")
        ic(data_path)

        if not Path(data_path).exists():
            self.logger.error(f"Data file not found: {data_path}")
            raise FileNotFoundError(f"Data file not found: {data_path}")

        # Load with progress indication
        with self.progress.progress_context("Loading data") as progress:
            task = progress.add_task("Reading CSV...", total=100)
            df = pd.read_csv(data_path)
            progress.update(task, advance=100)

        self.logger.success(f"Data loaded: {len(df):,} movies")
        ic(df.shape, df.columns.tolist())

        # Display data summary table
        display_table(
            "Data Summary",
            ["Metric", "Value"],
            [
                ["Total Movies", f"{len(df):,}"],
                ["Columns", str(len(df.columns))],
                ["Memory Usage", f"{df.memory_usage().sum() / 1024**2:.1f} MB"],
                ["Missing Values", str(df.isnull().sum().sum())],
                ["Avg Rating", f"{df[self.TARGET_COLUMN].mean():.2f}"],
                [
                    "Rating Range",
                    f"{df[self.TARGET_COLUMN].min():.1f} - {df[self.TARGET_COLUMN].max():.1f}",
                ],
            ],
        )

        return df

    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Enhanced feature preparation with debugging"""
        self.logger.info("Preparing features...")
        ic("Feature preparation started")

        # Check available features
        available_features = [col for col in self.BASE_FEATURES if col in df.columns]
        missing_features = [col for col in self.BASE_FEATURES if col not in df.columns]

        ic(available_features, missing_features)

        if not available_features:
            self.logger.error(f"No required features found! Need: {self.BASE_FEATURES}")
            raise ValueError(f"Required features missing: {self.BASE_FEATURES}")

        if missing_features:
            self.logger.warning(f"Missing features: {missing_features}")

        # Feature processing with progress
        self.logger.info("Processing features...")
        X = df[available_features].copy()

        # Enhanced debugging of feature statistics
        if HAS_ICECREAM:
            for feature in available_features:
                ic(feature)
                ic(X[feature].describe())
                ic(X[feature].isnull().sum())

        # Fill missing values with progress tracking
        with self.progress.progress_context("Filling missing values") as progress:
            task = progress.add_task("Processing...", total=len(available_features))
            for feature in available_features:
                median_val = X[feature].median()
                X[feature] = X[feature].fillna(median_val)
                progress.update(task, advance=1)
                ic(f"Filled {feature} missing values with {median_val}")

        # Target variable
        y = df[self.TARGET_COLUMN].values
        ic(y.shape, y.min(), y.max(), y.mean())

        # Store feature names
        self.feature_names = available_features

        self.logger.success(
            f"Features prepared: {len(X)} samples, {len(available_features)} features"
        )

        # Feature correlation analysis (enhanced output)
        if HAS_RICH:
            correlations = []
            for feature in available_features:
                corr = np.corrcoef(X[feature], y)[0, 1]
                correlations.append([feature, f"{corr:.3f}"])

            display_table(
                "Feature-Target Correlations", ["Feature", "Correlation"], correlations
            )

        return X.values, y

    def train_model(
        self, X: np.ndarray, y: np.ndarray, model_type: str = "random_forest"
    ) -> Dict[str, float]:
        """Enhanced model training with progress and debugging"""
        self.logger.info(f"Training {model_type} model...")
        ic(X.shape, y.shape, model_type)

        # Data splitting with enhanced logging
        self.logger.info("Splitting data...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        ic(X_train.shape, X_test.shape, y_train.shape, y_test.shape)

        # Feature scaling with progress
        self.logger.info("Scaling features...")
        from sklearn.preprocessing import StandardScaler

        self.scaler = StandardScaler()

        with self.progress.progress_context("Scaling features") as progress:
            task = progress.add_task("Fitting scaler...", total=100)
            X_train_scaled = self.scaler.fit_transform(X_train)
            progress.update(task, advance=50)
            X_test_scaled = self.scaler.transform(X_test)
            progress.update(task, advance=50)

        ic("Feature scaling completed")

        # Model selection with enhanced output
        self.logger.info(f"Initializing {model_type} model...")
        if model_type == "random_forest":
            self.model = RandomForestRegressor(
                n_estimators=100, random_state=42, n_jobs=-1  # Use all CPU cores
            )
        elif model_type == "linear_regression":
            self.model = LinearRegression()
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

        ic(self.model.get_params())

        # Training with progress tracking
        self.logger.info("Training model... (this may take a moment)")
        start_time = datetime.now()

        # For RandomForest, we can track progress using n_estimators
        if model_type == "random_forest" and HAS_TQDM:
            # Custom progress tracking for RandomForest
            estimators_list = []
            for i in self.progress.track(range(100), "Training estimators"):
                temp_model = RandomForestRegressor(
                    n_estimators=1, random_state=42 + i, warm_start=False
                )
                temp_model.fit(X_train_scaled, y_train)
                estimators_list.extend(temp_model.estimators_)

            # Combine all estimators
            self.model.estimators_ = estimators_list
            self.model.n_estimators = len(estimators_list)
        else:
            self.model.fit(X_train_scaled, y_train)

        training_time = (datetime.now() - start_time).total_seconds()
        self.logger.success(f"Training completed in {training_time:.2f} seconds")
        ic(training_time)

        # Enhanced prediction and evaluation
        self.logger.info("Evaluating model...")
        y_pred = self.model.predict(X_test_scaled)

        # Calculate metrics
        metrics = {
            "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
            "mae": mean_absolute_error(y_test, y_pred),
            "r2_score": r2_score(y_test, y_pred),
        }

        ic(metrics)

        # Enhanced metrics display
        display_table(
            "Model Performance",
            ["Metric", "Value", "Interpretation"],
            [
                ["RMSE", f"{metrics['rmse']:.4f}", "Lower is better"],
                ["MAE", f"{metrics['mae']:.4f}", "Lower is better"],
                [
                    "R² Score",
                    f"{metrics['r2_score']:.4f}",
                    "Higher is better (max 1.0)",
                ],
                ["Training Time", f"{training_time:.2f}s", "Efficiency measure"],
            ],
        )

        # Feature importance (for RandomForest)
        if hasattr(self.model, "feature_importances_"):
            importances = []
            for i, importance in enumerate(self.model.feature_importances_):
                importances.append([self.feature_names[i], f"{importance:.4f}"])

            display_table("Feature Importances", ["Feature", "Importance"], importances)
            ic(dict(zip(self.feature_names, self.model.feature_importances_)))

        # MLflow logging with enhanced error handling
        try:
            with mlflow.start_run():
                # Parameters
                mlflow.log_param("model_type", model_type)
                mlflow.log_param("features", self.feature_names)
                mlflow.log_param("n_features", len(self.feature_names))
                mlflow.log_param("training_time", training_time)

                # Metrics
                for metric_name, metric_value in metrics.items():
                    mlflow.log_metric(metric_name, metric_value)

                # Model logging
                input_example = pd.DataFrame(
                    X_train_scaled[:5], columns=self.feature_names
                )

                mlflow.sklearn.log_model(
                    self.model,
                    "model",
                    input_example=input_example,
                    registered_model_name=f"{model_type}_movie_rating_enhanced",
                )

                self.logger.success("MLflow logging completed")

        except Exception as e:
            self.logger.warning(f"MLflow logging failed: {e}")
            ic(e)

        return metrics

    def save_model(self) -> Dict[str, str]:
        """Enhanced model saving with progress and validation"""
        if self.model is None:
            self.logger.error("No trained model to save!")
            raise ValueError("No trained model found")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_filename = (
            f"enhanced_{type(self.model).__name__.lower()}_{timestamp}.joblib"
        )
        scaler_filename = f"enhanced_scaler_{timestamp}.joblib"

        model_path = self.models_dir / model_filename
        scaler_path = self.models_dir / scaler_filename

        # Enhanced model info
        model_info = {
            "model": self.model,
            "feature_names": self.feature_names,
            "model_type": type(self.model).__name__,
            "timestamp": timestamp,
            "enhanced": True,
            "version": "2.0",
        }

        # Save with progress tracking
        with self.progress.progress_context("Saving model") as progress:
            task = progress.add_task("Saving files...", total=100)

            joblib.dump(model_info, model_path)
            progress.update(task, advance=50)
            ic(f"Model saved: {model_path}")

            if self.scaler:
                joblib.dump(self.scaler, scaler_path)
            progress.update(task, advance=50)
            ic(f"Scaler saved: {scaler_path}")

        self.logger.success(f"Model saved successfully!")

        # Validation check
        try:
            test_load = joblib.load(model_path)
            self.logger.success("Model file validation passed")
            ic("Model save validation successful")
        except Exception as e:
            self.logger.error(f"Model file validation failed: {e}")
            ic(e)

        return {
            "model_path": str(model_path),
            "scaler_path": str(scaler_path) if self.scaler else None,
            "feature_names": self.feature_names,
            "timestamp": timestamp,
        }


def enhanced_training_pipeline(
    data_path: str = "data/processed/movies_with_ratings.csv",
    model_type: str = "random_forest",
):
    """Enhanced training pipeline with full UX improvements"""

    logger = EnhancedLogger("Pipeline")
    logger.info("🚀 Starting Enhanced MLOps Training Pipeline")

    try:
        # Initialize trainer
        trainer = EnhancedMovieRatingTrainer()

        # Load data
        df = trainer.load_data(data_path)

        # Prepare features
        X, y = trainer.prepare_features(df)

        # Train model
        metrics = trainer.train_model(X, y, model_type=model_type)

        # Save model
        model_info = trainer.save_model()

        # Final summary
        enhanced_print(
            "\n🎉 [bold green]Training Pipeline Completed Successfully![/bold green]"
        )

        display_table(
            "Pipeline Results",
            ["Component", "Status", "Details"],
            [
                ["Data Loading", "✅ Success", f"{len(df):,} movies"],
                [
                    "Feature Prep",
                    "✅ Success",
                    f"{len(trainer.feature_names)} features",
                ],
                ["Model Training", "✅ Success", f"RMSE: {metrics['rmse']:.4f}"],
                ["Model Saving", "✅ Success", model_info["model_path"]],
                ["MLflow Logging", "✅ Success", trainer.experiment_name],
            ],
        )

        logger.success("All pipeline steps completed!")
        return model_info

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        ic(e)
        raise


if __name__ == "__main__":
    # CLI support with fire
    if HAS_FIRE:
        import fire

        fire.Fire(
            {
                "train": enhanced_training_pipeline,
                "pipeline": enhanced_training_pipeline,
            }
        )
    else:
        # Fallback to direct execution
        enhanced_training_pipeline()
