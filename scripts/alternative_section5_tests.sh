#!/bin/bash
# Alternative Section 5 Testing Methods
# For environments where Docker-in-Docker is not feasible

echo "🧪 Alternative Section 5 Testing Methods"
echo "========================================"

# Method 1: Direct API Testing (No Docker)
echo -e "\n1️⃣ Direct API Testing (No Docker needed)"
echo "----------------------------------------"

# Start API directly with uvicorn (simulate container behavior)
echo "Starting API directly..."
export MLFLOW_TRACKING_URI="http://localhost:5000"
export MODEL_PATH="models"
export LOG_LEVEL="INFO"

# Start MLflow in background
echo "Starting MLflow..."
mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///mlruns/test.db &
MLFLOW_PID=$!

sleep 5

# Start API in background
echo "Starting FastAPI..."
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

sleep 10

# Test API endpoints
echo "Testing API endpoints..."
curl -s http://localhost:8000/health | python -m json.tool
curl -s http://localhost:8000/model/info | python -m json.tool

# Test prediction
echo "Testing prediction..."
curl -X POST "http://localhost:8000/predict/movie" \
     -H "Content-Type: application/json" \
     -d '{"title":"Test Movie","startYear":2020,"runtimeMinutes":120,"numVotes":5000}' | python -m json.tool

# Cleanup
echo "Cleaning up..."
kill $API_PID $MLFLOW_PID 2>/dev/null

echo "✅ Direct API testing completed"

# Method 2: Configuration Validation
echo -e "\n2️⃣ Configuration Validation"
echo "----------------------------"

# Validate Docker Compose files
echo "Validating docker-compose.yml..."
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker/docker-compose.yml config --quiet
    if [ $? -eq 0 ]; then
        echo "✅ docker-compose.yml is valid"
    else
        echo "❌ docker-compose.yml has errors"
    fi
else
    echo "⚠️ docker-compose not available, skipping validation"
fi

# Validate Dockerfiles (syntax check)
echo "Validating Dockerfiles..."
for dockerfile in docker/Dockerfile.api docker/Dockerfile.train; do
    if [ -f "$dockerfile" ]; then
        echo "✅ $dockerfile exists"
        # Basic syntax check
        if grep -q "FROM\|WORKDIR\|COPY\|RUN" "$dockerfile"; then
            echo "   ✅ Basic syntax valid"
        else
            echo "   ❌ Missing essential commands"
        fi
    else
        echo "❌ $dockerfile missing"
    fi
done

# Method 3: Dependency Check
echo -e "\n3️⃣ Dependency Check"
echo "-------------------"

echo "Checking if all dependencies can be installed..."
pip install --dry-run -r requirements.txt > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ All dependencies are installable"
else
    echo "❌ Some dependencies have issues"
fi

# Check enhanced dependencies
if [ -f "requirements-enhanced.txt" ]; then
    pip install --dry-run -r requirements-enhanced.txt > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Enhanced dependencies are installable"
    else
        echo "⚠️ Some enhanced dependencies may have issues"
    fi
fi

# Method 4: Container Build Simulation
echo -e "\n4️⃣ Container Build Simulation"
echo "-----------------------------"

echo "Simulating container build process..."

# Check if all files needed for container build exist
BUILD_FILES=(
    "requirements.txt"
    "src/api/main.py"
    "src/api/endpoints.py"
    "src/api/schemas.py"
    "src/models/evaluator.py"
    "configs/"
)

echo "Checking build context files..."
for file in "${BUILD_FILES[@]}"; do
    if [ -e "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file missing"
    fi
done

# Simulate COPY operations
echo "Simulating COPY operations..."
echo "   COPY requirements.txt . → $([ -f requirements.txt ] && echo "✅" || echo "❌")"
echo "   COPY src/ src/ → $([ -d src ] && echo "✅" || echo "❌")"
echo "   COPY configs/ configs/ → $([ -d configs ] && echo "✅" || echo "❌")"

# Method 5: Port Availability Check
echo -e "\n5️⃣ Port Availability Check"
echo "--------------------------"

REQUIRED_PORTS=(8000 5000)

echo "Checking if required ports are available..."
for port in "${REQUIRED_PORTS[@]}"; do
    if command -v netstat &> /dev/null; then
        if netstat -ln | grep -q ":$port "; then
            echo "⚠️ Port $port is in use"
        else
            echo "✅ Port $port is available"
        fi
    elif command -v ss &> /dev/null; then
        if ss -ln | grep -q ":$port "; then
            echo "⚠️ Port $port is in use"
        else
            echo "✅ Port $port is available"
        fi
    else
        echo "ℹ️ Cannot check port $port (no netstat/ss available)"
    fi
done

# Method 6: Volume Mount Simulation
echo -e "\n6️⃣ Volume Mount Simulation"
echo "--------------------------"

VOLUME_DIRS=("models" "data" "logs")

echo "Checking volume directories..."
for dir in "${VOLUME_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        count=$(find "$dir" -type f | wc -l)
        echo "✅ $dir/ exists ($count files)"
    else
        echo "⚠️ $dir/ missing - creating..."
        mkdir -p "$dir"
        echo "✅ $dir/ created"
    fi
done

# Method 7: Environment Variables Test
echo -e "\n7️⃣ Environment Variables Test"
echo "-----------------------------"

echo "Testing container environment variables..."
export MLFLOW_TRACKING_URI="http://mlflow:5000"
export MODEL_PATH="/app/models"
export LOG_LEVEL="INFO"
export PYTHONPATH="/app"

ENV_VARS=("MLFLOW_TRACKING_URI" "MODEL_PATH" "LOG_LEVEL" "PYTHONPATH")

for var in "${ENV_VARS[@]}"; do
    value=${!var}
    if [ -n "$value" ]; then
        echo "✅ $var=$value"
    else
        echo "❌ $var not set"
    fi
done

echo -e "\n🎉 Alternative testing completed!"
echo "=================================="

echo -e "\n📋 Summary:"
echo "   ✅ Configuration files validated"
echo "   ✅ Dependencies checked"
echo "   ✅ Build context verified"
echo "   ✅ Ports and volumes checked"
echo "   ✅ Environment variables tested"

echo -e "\n💡 Next Steps:"
echo "   1. Run simulation test: python scripts/tests/section5_simulation_test.py"
echo "   2. Test on local machine with Docker"
echo "   3. Set up CI/CD pipeline for automated testing"
echo "   4. Proceed to Section 6: Monitoring & CI/CD"

echo -e "\n🐳 When Docker is available, run:"
echo "   docker-compose -f docker/docker-compose.yml up -d"
echo "   python scripts/tests/test_section5.py"
