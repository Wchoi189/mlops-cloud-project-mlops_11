import json
import os
import platform
import subprocess
import sys
from pathlib import Path


def run_command(cmd, shell=False):
    """Safely run a command and return output"""
    try:
        if isinstance(cmd, str) and not shell:
            cmd = cmd.split()
        result = subprocess.run(cmd, capture_output=True, text=True, shell=shell)
        return result.stdout.strip() if result.returncode == 0 else "Not available"
    except Exception as e:
        return f"Error: {str(e)}"


def get_wsl_environment_info():
    """Extract comprehensive WSL environment information"""

    env_info = {}

    # === SYSTEM INFORMATION ===
    env_info["system"] = {
        "wsl_version": run_command("wsl --version"),
        "wsl_distro": os.environ.get("WSL_DISTRO_NAME", "Unknown"),
        "kernel": run_command("uname -r"),
        "os_release": run_command("cat /etc/os-release"),
        "architecture": platform.machine(),
        "hostname": platform.node(),
    }

    # === HARDWARE RESOURCES ===
    env_info["hardware"] = {
        "cpu_info": run_command("lscpu"),
        "memory_total": run_command("free -h | grep Mem | awk '{print $2}'"),
        "memory_available": run_command("free -h | grep Mem | awk '{print $7}'"),
        "disk_space": run_command("df -h /"),
        "gpu_info": run_command(
            "nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader,nounits"
        ),
    }

    # === PYTHON ENVIRONMENT ===
    env_info["python"] = {
        "version": sys.version,
        "executable": sys.executable,
        "path": sys.path,
        "pip_version": run_command("pip --version"),
        "conda_info": (
            run_command("conda info --json")
            if run_command("which conda") != "Not available"
            else "Not installed"
        ),
        "virtual_env": os.environ.get("VIRTUAL_ENV", "None"),
    }

    # === ML/AI LIBRARIES ===
    ml_packages = [
        "numpy",
        "pandas",
        "scikit-learn",
        "matplotlib",
        "seaborn",
        "tensorflow",
        "torch",
        "transformers",
        "opencv-python",
        "jupyter",
        "ipython",
        "plotly",
        "scipy",
        "statsmodels",
    ]

    env_info["ml_libraries"] = {}
    for package in ml_packages:
        try:
            result = run_command(f"pip show {package}")
            if "Version:" in result:
                version = [
                    line for line in result.split("\n") if line.startswith("Version:")
                ][0]
                env_info["ml_libraries"][package] = version.split(": ")[1]
            else:
                env_info["ml_libraries"][package] = "Not installed"
        except:
            env_info["ml_libraries"][package] = "Not installed"

    # === DEVELOPMENT TOOLS ===
    env_info["dev_tools"] = {
        "git_version": run_command("git --version"),
        "docker_version": run_command("docker --version"),
        "cuda_version": run_command("nvcc --version"),
        "gcc_version": run_command("gcc --version"),
        "make_version": run_command("make --version"),
    }

    # === ENVIRONMENT VARIABLES ===
    important_env_vars = [
        "PATH",
        "PYTHONPATH",
        "CUDA_VISIBLE_DEVICES",
        "CUDA_HOME",
        "LD_LIBRARY_PATH",
        "HOME",
        "USER",
        "SHELL",
    ]

    env_info["environment_variables"] = {
        var: os.environ.get(var, "Not set") for var in important_env_vars
    }

    # === STORAGE INFORMATION ===
    env_info["storage"] = {
        "home_directory": str(Path.home()),
        "current_directory": os.getcwd(),
        "temp_directory": os.environ.get("TMPDIR", "/tmp"),
        "datasets_path": os.environ.get("DATASETS_PATH", "Not set"),
    }

    return env_info


def save_environment_info(filename="wsl_ml_environment.json"):
    """Save environment information to JSON file"""
    env_info = get_wsl_environment_info()

    with open(filename, "w") as f:
        json.dump(env_info, f, indent=2)

    print(f"Environment information saved to {filename}")
    return env_info


def print_summary(env_info):
    """Print a concise summary of key information"""
    print("🔍 WSL ML Environment Summary")
    print("=" * 50)

    print(f"📊 System: {env_info['system']['wsl_distro']} on WSL")
    print(f"🐍 Python: {env_info['python']['version'].split()[0]}")
    print(f"💾 Memory: {env_info['hardware']['memory_total']} total")
    print(f"🎯 GPU: {env_info['hardware']['gpu_info']}")

    print("\n📦 Key ML Libraries:")
    key_libs = ["numpy", "pandas", "scikit-learn", "tensorflow", "torch"]
    for lib in key_libs:
        status = env_info["ml_libraries"].get(lib, "Not installed")
        print(f"  • {lib}: {status}")

    print(f"\n🔧 Virtual Environment: {env_info['python']['virtual_env']}")
    print(f"📁 Working Directory: {env_info['storage']['current_directory']}")


if __name__ == "__main__":
    # Extract and save environment information
    env_info = save_environment_info()

    # Print summary
    print_summary(env_info)
