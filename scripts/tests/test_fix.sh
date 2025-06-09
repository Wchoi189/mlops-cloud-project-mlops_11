# 1. Create test model
mkdir -p models
python -c "
import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

model = RandomForestRegressor(n_estimators=10, random_state=42)
X = np.random.rand(100, 3)
y = np.random.rand(100) * 10
model.fit(X, y)

scaler = StandardScaler()
scaler.fit(X)

model_data = {
    'model': model,
    'scaler': scaler,
    'feature_names': ['startYear', 'runtimeMinutes', 'numVotes'],
    'model_info': {'model_type': 'RandomForestRegressor', 'features': 3}
}
joblib.dump(model_data, 'models/latest_model.joblib')
"

# 2. Test Docker setup
cd docker && docker compose up -d

# 3. Test API
curl -X POST "http://localhost:8000/predict/movie" \
     -H "Content-Type: application/json" \
     -d '{"title":"Test","startYear":2020,"runtimeMinutes":120,"numVotes":5000}'