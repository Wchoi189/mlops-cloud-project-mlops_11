import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import os

print('Creating Docker model...')
os.makedirs('/app/models', exist_ok=True)
np.random.seed(42)
X = np.random.rand(50, 3)
X[:, 0] = 2000 + X[:, 0] * 24
X[:, 1] = 90 + X[:, 1] * 90
X[:, 2] = 5000 + X[:, 2] * 995000
y = 5 + np.random.rand(50) * 5
model = RandomForestRegressor(n_estimators=5, random_state=42)
model.fit(X, y)
model_data = {'model': model, 'feature_names': ['startYear', 'runtimeMinutes', 'numVotes'], 'model_info': {'model_type': 'RandomForestRegressor', 'version': 'docker-1.0'}}
joblib.dump(model_data, '/app/models/docker_model2.joblib')
print('✅ Docker model created')