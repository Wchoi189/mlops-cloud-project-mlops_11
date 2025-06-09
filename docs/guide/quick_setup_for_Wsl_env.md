# 🚀 Quick Setup Guide for Windows WSL Environment

## 📋 Overview

This guide will help you set up the MLOps project quickly on Windows WSL with minimal dependencies.

## ⚡ Step 1: Create Virtual Environment (30 seconds)

```bash
# Navigate to project directory
cd mlops-cloud-project-mlops_11

# Create lightweight virtual environment
python3 -m venv mlops-env-light

# Activate environment
source mlops-env-light/bin/activate

# Upgrade pip for faster downloads
pip install --upgrade pip
```

## ⚡ Step 2: Install Minimal Dependencies (2-3 minutes)

```bash
# Install only essential packages
pip install -r requirements-minimal.txt

# Verify installation
python -c "import pandas, numpy, sklearn, fastapi, mlflow; print('✅ Core packages installed successfully!')"
```

## ⚡ Step 3: Test Basic Functionality (1 minute)

```bash
# Test data loading
python -c "
from src.data.data_loader import IMDbDataLoader
loader = IMDbDataLoader()
print('✅ Data loader works!')
"

# Test API
python -c "
from fastapi import FastAPI
app = FastAPI()
print('✅ FastAPI works!')
"
```

## 📊 Installation Size Comparison

| Package Set | Size | Time | Core Features |
|-------------|------|------|---------------|
| **Original requirements.txt** | ~2.5GB | 15-30 min | All features |
| **requirements-minimal.txt** | ~150MB | 2-3 min | Core MLOps |
| **Enhanced (optional)** | +50MB | +1 min | Better UX |

## 🔧 Add Enhanced Features Later (Optional)

Only install these if you want better UX:

```bash
# Better debugging and progress bars
pip install icecream tqdm rich fire

# Basic plotting (if needed)
pip install matplotlib seaborn

# PyTorch (only if doing deep learning)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

## 🎯 What's Included in Minimal Setup

### ✅ Core Functionality Available

- ✅ **Data Pipeline**: Load and process IMDB data
- ✅ **Model Training**: RandomForest, LinearRegression with sklearn
- ✅ **API Serving**: FastAPI with prediction endpoints
- ✅ **MLflow Integration**: Experiment tracking
- ✅ **Model Evaluation**: Basic metrics and evaluation
- ✅ **Docker Support**: All Dockerfiles will work

### ⚠️ Not Included (Add Later If Needed)

- ❌ **Deep Learning**: No PyTorch/TensorFlow (add separately)
- ❌ **Advanced NLP**: No NLTK/transformers (not needed for basic rating prediction)
- ❌ **Heavy Monitoring**: No Evidently (can add later)
- ❌ **Workflow Orchestration**: No Airflow/Prefect (basic scripts work fine)
- ❌ **Advanced Visualization**: No Plotly (matplotlib available if you add it)

## 🚀 Quick Start Commands

```bash
# 1. Install minimal dependencies (2-3 minutes)
pip install -r requirements-minimal.txt

# 2. Run Section 1 (Data Pipeline)
python scripts/validate_data.py

# 3. Run Section 2 (Preprocessing)
python scripts/test_preprocessing.py

# 4. Run Section 3 (Model Training)
python scripts/train_model.py --quick

# 5. Run Section 4 (API)
uvicorn src.api.main:app --port 8000
```

## 🔍 Troubleshooting WSL Issues

### Common WSL Problems

```bash
# Fix: Python not found
sudo apt update && sudo apt install python3 python3-pip python3-venv

# Fix: pip issues
python3 -m pip install --upgrade pip

# Fix: Build tools missing (if compilation errors)
sudo apt install build-essential python3-dev

# Fix: Virtual environment issues
rm -rf mlops-env-light && python3 -m venv mlops-env-light
```

### Performance Tips for WSL

```bash
# Use WSL2 (much faster than WSL1)
wsl --set-version Ubuntu 2

# Store project in WSL filesystem (not Windows drive)
# ✅ Good: /home/username/projects/mlops-cloud-project-mlops_11
# ❌ Slow: /mnt/c/Users/username/projects/mlops-cloud-project-mlops_11
```

## 🎯 What Each Minimal Package Does

| Package | Size | Purpose | Alternative |
|---------|------|---------|-------------|
| **pandas** | ~15MB | Data manipulation | None - essential |
| **numpy** | ~10MB | Numerical computing | None - essential |
| **scikit-learn** | ~30MB | Machine learning | None - essential |
| **fastapi** | ~5MB | API framework | Flask (lighter but less features) |
| **uvicorn** | ~2MB | ASGI server | None - needed for FastAPI |
| **mlflow** | ~50MB | Experiment tracking | None - core to MLOps |
| **pydantic** | ~3MB | Data validation | None - needed for FastAPI |
| **requests** | ~2MB | HTTP requests | None - essential utility |
| **python-dotenv** | ~1MB | Environment variables | Manual env loading |
| **joblib** | ~2MB | Model serialization | pickle (built-in, less features) |

## 🔄 Upgrade Path

When you need more features:

```bash
# Stage 1: Minimal (2-3 minutes)
pip install -r requirements-minimal.txt

# Stage 2: Enhanced UX (+1 minute)
pip install icecream tqdm rich fire

# Stage 3: Visualization (+1 minute)
pip install matplotlib seaborn

# Stage 4: Deep Learning (+5-10 minutes)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Stage 5: Advanced Features (as needed)
pip install evidently apache-airflow transformers
```

## ✅ Verification Commands

```bash
# Check installation size
pip list | wc -l  # Should show ~15-20 packages instead of 50+

# Check core functionality
python -c "
import pandas as pd
import numpy as np
import sklearn
import fastapi
import mlflow
print('✅ All core packages working!')
print(f'Pandas: {pd.__version__}')
print(f'FastAPI: {fastapi.__version__}')
print(f'MLflow: {mlflow.__version__}')
"

# Test basic MLOps pipeline
python scripts/tests/test_section1.py --quick
```

## 🎉 Success Criteria

You'll know the minimal setup worked when:

- ✅ Installation completes in under 5 minutes
- ✅ Total package count is under 25 (vs 50+ in full setup)
- ✅ All Section 1-4 basic tests pass
- ✅ API starts successfully on port 8000
- ✅ Model training runs without errors

This minimal setup gives you 80% of the functionality with 20% of the installation time!
