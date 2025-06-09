import mlflow
import mlflow.sklearn
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier

# Set tracking URI
mlflow.set_tracking_uri("http://localhost:5000")

# Create a simple experiment
with mlflow.start_run():
    # Generate sample data
    X, y = make_classification(n_samples=100, n_features=4, random_state=42)

    # Train model
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)

    # Log parameters and metrics
    mlflow.log_param("n_estimators", 10)
    mlflow.log_metric("accuracy", 0.95)

    # Log model
    mlflow.sklearn.log_model(model, "model")

print("Experiment completed!")
