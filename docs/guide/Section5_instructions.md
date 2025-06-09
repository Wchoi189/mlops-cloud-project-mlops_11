# 🐳 Section 5: Docker Containerization - Complete Implementation Guide

## 📋 Overview

Section 5 containerizes your MLOps pipeline using Docker, making it portable, scalable, and production-ready. We've also integrated enhanced libraries (icecream, tqdm, fire, rich) for better developer experience.

## 🆕 What's New in Section 5

### 🐳 Docker Components

1. **API Container** (`docker/Dockerfile.api`) - FastAPI서비스 컨테이너화
2. **Training Container** (`docker/Dockerfile.train`) - 모델 훈련 파이프라인 컨테이너화
3. **Multi-Service Orchestration** (`docker/docker-compose.yml`) - 전체 스택 관리
4. **Production Config** (`docker/docker-compose.prod.yml`) - 프로덕션 최적화 설정

### 🎨 Enhanced Developer Experience

1. **icecream** - Better debugging: `ic()` instead of `print()`
2. **tqdm** - Progress bars for data processing and training
3. **fire** - Automatic CLI generation from Python functions
4. **rich** - Beautiful terminal output and tables

## 🚀 Quick Start

### Step 1: Install Enhanced Dependencies (Optional but Recommended)

```bash
# Install enhanced libraries for better UX
pip install icecream tqdm fire rich

# Or install all enhanced dependencies
pip install -r requirements-enhanced.txt
```

### Step 2: Quick Docker Test

```bash
# Quick validation (no building)
python scripts/tests/test_section5.py --quick

# Full test with building (takes 5-10 minutes)
python scripts/tests/test_section5.py
```

### Step 3: Build and Deploy

```bash
# Option A: Using Docker Compose (Recommended)
cd docker
docker-compose up --build -d

# Option B: Using the Quick Start Script
python scripts/docker_quick_start.py

# Option C: Using Enhanced Makefile
make -f Makefile.docker docker-run
```

### Step 4: Verify Deployment

```bash
# Check service status
curl http://localhost:8000/health
curl http://localhost:5000/health

# Test movie prediction
curl -X POST "http://localhost:8000/predict/movie" \
     -H "Content-Type: application/json" \
     -d '{"title":"Test Movie","startYear":2020,"runtimeMinutes":120,"numVotes":5000}'

# Access web interfaces
# API Documentation: http://localhost:8000/docs
# MLflow UI: http://localhost:5000
```

## 📊 Service Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   nginx:80      │    │     api:8000    │    │   mlflow:5000   │
│ (Load Balancer) │───▶│  (FastAPI App)  │───▶│ (Tracking UI)   │
│   [Optional]    │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  trainer:batch  │
                       │ (Training Jobs) │
                       │   [On-demand]   │
                       └─────────────────┘
```

## 🔧 Available Commands

### Docker Compose Commands

```bash
# Start all services
docker-compose up -d

# Start with training
docker-compose --profile training up -d

# View logs
docker-compose logs -f api
docker-compose logs -f mlflow

# Stop services
docker-compose down

# Cleanup everything
docker-compose down --volumes --remove-orphans
```

### Enhanced Makefile Commands

```bash
make -f Makefile.docker docker-help     # Show all commands
make -f Makefile.docker docker-build    # Build images
make -f Makefile.docker docker-run      # Start services
make -f Makefile.docker docker-logs     # View logs
make -f Makefile.docker docker-stop     # Stop services
make -f Makefile.docker docker-health   # Check health
make -f Makefile.docker docker-clean    # Cleanup
```

### Enhanced CLI with Fire

```bash
# Enhanced training with progress bars
python src/utils/enhanced.py train --model_type=random_forest

# Quick predictions with rich output
python src/utils/enhanced.py predict --title="Inception" --year=2010 --runtime=148

# System status with tables
python src/utils/enhanced.py cli_class status

# Docker status check
python src/utils/enhanced.py docker_status
```

## 🧪 Testing & Validation

### Automated Testing

```bash
# Full Section 5 test suite
python scripts/tests/test_section5.py

# Quick validation only
python scripts/tests/test_section5.py --quick

# Enhanced API testing
python scripts/quick_api_test.py
```

### Manual Validation

```bash
# 1. Check Docker images
docker images | grep mlops

# 2. Check running containers
docker ps

# 3. Test API endpoints
curl http://localhost:8000/
curl http://localhost:8000/health
curl http://localhost:8000/model/info

# 4. Test prediction
curl -X POST "http://localhost:8000/predict/movie" \
     -H "Content-Type: application/json" \
     -d '{"title":"The Dark Knight","startYear":2008,"runtimeMinutes":152,"numVotes":2500000}'
```

## 🎨 Enhanced Features Demo

### Better Debugging with icecream

```python
# Instead of print statements
from src.utils.enhanced import ic

data = {"model": "RandomForest", "accuracy": 0.85}
ic(data)  # 🐛 DEBUG | data: {'model': 'RandomForest', 'accuracy': 0.85}

# Debug model training
ic(X.shape, y.shape, model_type)
```

### Progress Bars with tqdm

```python
from src.utils.enhanced import track_progress

# Training with progress
for epoch in track_progress(range(100), "Training model"):
    # training code here
    pass
```

### Rich Tables and Output

```python
from src.utils.enhanced import display_table

display_table(
    "Model Results",
    ["Model", "RMSE", "R²"],
    [
        ["RandomForest", "0.691", "0.314"],
        ["LinearRegression", "0.728", "0.289"]
    ]
)
```

### Fire CLI Generation

```python
# Automatic CLI from any function
import fire

def train_model(model_type="random_forest", epochs=10):
    # training code
    return {"status": "completed"}

if __name__ == "__main__":
    fire.Fire(train_model)

# Usage: python script.py --model_type=linear --epochs=50
```

## 🔍 Troubleshooting

### Common Issues

#### Docker Build Fails

```bash
# Clear Docker cache
docker system prune -f

# Rebuild without cache
docker-compose build --no-cache

# Check available space
docker system df
```

#### Services Won't Start

```bash
# Check port conflicts
lsof -i :8000
lsof -i :5000

# Check Docker daemon
docker info

# View detailed logs
docker-compose logs --tail=50 api
```

#### API Not Responding

```bash
# Check container status
docker ps

# Enter container for debugging
docker-compose exec api bash

# Check model files are mounted
docker-compose exec api ls -la /app/models/
```

#### Models Not Loading

```bash
# Verify model files exist
ls -la models/

# Check file permissions
docker-compose exec api ls -la /app/models/

# Manual model test
docker-compose exec api python -c "
from src.models.evaluator import ModelEvaluator
evaluator = ModelEvaluator()
print('Available models:', evaluator.get_model_info())
"
```

## 📈 Performance Optimization

### Production Deployment

```bash
# Use production configuration
docker-compose -f docker/docker-compose.prod.yml up -d

# With monitoring
docker-compose -f docker/docker-compose.prod.yml --profile monitoring up -d

# With load balancing
docker-compose -f docker/docker-compose.prod.yml --profile production up -d
```

### Resource Limits

```yaml
# In docker-compose.prod.yml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '2.0'
    reservations:
      memory: 1G
      cpus: '1.0'
```

### Health Checks

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 15s
```

## 🎯 Next Steps After Section 5

1. **Section 6: Monitoring & CI/CD**
   - Prometheus/Grafana monitoring
   - GitHub Actions CI/CD
   - Automated testing pipelines

2. **Production Deployment**
   - Cloud deployment (AWS/GCP/Azure)
   - Kubernetes orchestration
   - Auto-scaling configuration

3. **Advanced Features**
   - Model versioning
   - A/B testing
   - Performance monitoring

## 📚 Key Files Created

- `docker/Dockerfile.api` - API 컨테이너 설정
- `docker/Dockerfile.train` - 훈련 컨테이너 설정
- `docker/docker-compose.yml` - 개발용 멀티 서비스
- `docker/docker-compose.prod.yml` - 프로덕션 설정
- `scripts/tests/test_section5.py` - Docker 테스트 스위트
- `scripts/docker_quick_start.py` - 원클릭 Docker 배포
- `Makefile.docker` - Docker 관리 명령어
- `requirements-enhanced.txt` - 향상된 개발자 경험 라이브러리
- `src/utils/enhanced.py` - icecream, tqdm, fire, rich 통합
- `src/models/enhanced_trainer.py` - 향상된 훈련 파이프라인

## 💡 Enhanced Libraries Integration

### icecream - Better Debugging

```python
# Before: print debugging
print("Data shape:", X.shape)
print("Model type:", model_type)

# After: Enhanced debugging
from src.utils.enhanced import ic
ic(X.shape, model_type)  # 🐛 DEBUG | X.shape: (5764, 3), model_type: 'random_forest'
```

### tqdm - Progress Tracking

```python
# Before: No progress indication
for epoch in range(100):
    train_step()

# After: Visual progress bars
from src.utils.enhanced import track_progress
for epoch in track_progress(range(100), "Training model"):
    train_step()
```

### fire - Automatic CLI

```python
# Before: Manual argparse setup
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--model_type', default='random_forest')
args = parser.parse_args()

# After: Automatic CLI
import fire

def train(model_type='random_forest', epochs=10):
    return train_model(model_type, epochs)

if __name__ == '__main__':
    fire.Fire(train)  # Automatic CLI: python script.py --model_type=linear --epochs=50
```

### rich - Beautiful Output

```python
# Before: Plain text tables
print("Model Results:")
print("RandomForest: 0.691 RMSE")
print("Linear: 0.728 RMSE")

# After: Beautiful tables
from src.utils.enhanced import display_table
display_table(
    "Model Results",
    ["Model", "RMSE", "Status"],
    [
        ["RandomForest", "0.691", "✅ Best"],
        ["Linear", "0.728", "⚠️ Baseline"]
    ]
)
```

## 🔄 Development Workflow

### Daily Development with Docker

```bash
# 1. Start development environment
make -f Makefile.docker docker-run

# 2. Code changes (files are mounted, no rebuild needed)
# Edit src/api/main.py, src/models/trainer.py, etc.

# 3. Test changes
python scripts/quick_api_test.py

# 4. View logs
make -f Makefile.docker docker-logs-api

# 5. Restart if needed
make -f Makefile.docker docker-restart
```

### Enhanced Training Workflow

```bash
# 1. Use enhanced trainer with progress bars
python src/models/enhanced_trainer.py

# 2. Or use fire CLI
python src/models/enhanced_trainer.py train --model_type=random_forest

# 3. Quick CLI tools
python src/utils/enhanced.py predict --title="Inception" --year=2010

# 4. Debug with icecream
python -c "
from src.utils.enhanced import ic, tools
data = {'test': 'value'}
ic(data)
tools.debug_model_info(None, data)
"
```

## 🚀 Production Deployment

### Cloud Deployment Preparation

```bash
# 1. Test production configuration
docker-compose -f docker/docker-compose.prod.yml up -d

# 2. Build production images
docker build -f docker/Dockerfile.api -t your-registry/mlops-api:v1.0 .
docker build -f docker/Dockerfile.train -t your-registry/mlops-trainer:v1.0 .

# 3. Push to registry
docker push your-registry/mlops-api:v1.0
docker push your-registry/mlops-trainer:v1.0

# 4. Deploy to cloud (example for AWS ECS, GCP Cloud Run, etc.)
```

### Kubernetes Deployment (Future Section 6+)

```yaml
# Example Kubernetes deployment (preview)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mlops-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mlops-api
  template:
    metadata:
      labels:
        app: mlops-api
    spec:
      containers:
      - name: api
        image: your-registry/mlops-api:v1.0
        ports:
        - containerPort: 8000
        env:
        - name: MLFLOW_TRACKING_URI
          value: "http://mlflow-service:5000"
```

## 🎉 Section 5 Success Criteria

✅ **Docker Containerization Complete**

- [x] API containerized with Dockerfile.api
- [x] Training pipeline containerized with Dockerfile.train
- [x] Multi-service orchestration with docker-compose.yml
- [x] Production-ready configuration with docker-compose.prod.yml

✅ **Enhanced Developer Experience**

- [x] icecream for better debugging
- [x] tqdm for progress tracking
- [x] fire for automatic CLI generation
- [x] rich for beautiful terminal output

✅ **Testing & Validation**

- [x] Comprehensive test suite (test_section5.py)
- [x] Quick validation scripts
- [x] Health checks and monitoring

✅ **Production Readiness**

- [x] Resource limits and health checks
- [x] Volume mounts for persistence
- [x] Environment variable configuration
- [x] Logging and monitoring setup

## 📊 Performance Benchmarks (Expected)

| Metric | Development | Production |
|--------|-------------|------------|
| API Response Time | < 100ms | < 50ms |
| Container Start Time | < 30s | < 15s |
| Memory Usage (API) | ~512MB | ~1GB |
| Memory Usage (Training) | ~2GB | ~4GB |
| Model Load Time | < 5s | < 3s |

## 🎯 Ready for Section 6

With Section 5 complete, you now have:

1. **Fully Containerized MLOps Pipeline** 🐳
2. **Enhanced Developer Experience** 🎨
3. **Production-Ready Configuration** 🚀
4. **Comprehensive Testing** 🧪
5. **Beautiful CLI and Output** ✨

**Next Section 6 will focus on:**

- Monitoring with Prometheus/Grafana
- CI/CD with GitHub Actions
- Automated testing pipelines
- Performance monitoring and alerting

---

**🎉 Congratulations! Section 5 Docker Containerization is now complete and ready for deployment!**
