"""
Enhanced utilities with icecream, tqdm, fire, and rich
Better debugging, progress tracking, and CLI interfaces
"""

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
import importlib

# Force reload of logging module if there's a conflict
if 'logging' in sys.modules:
    importlib.reload(sys.modules['logging'])
import logging

# Enhanced libraries
try:
    from icecream import ic, install as ic_install
    HAS_ICECREAM = True
    # Setup icecream for better debugging
    if HAS_ICECREAM:
        ic_install()  # Make ic() available everywhere
        ic.configureOutput(prefix='🐛 DEBUG | ')
except ImportError:
    HAS_ICECREAM = False
    # Fallback to print if icecream not available
    def ic(*args):
        if args:
            print("DEBUG:", *args)
        return args[0] if len(args) == 1 else args

try:
    from tqdm import tqdm
    from tqdm.auto import tqdm as auto_tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    # Fallback iterator
    def tqdm(iterable, *args, **kwargs):
        return iterable
    auto_tqdm = tqdm

try:
    import fire
    HAS_FIRE = True
except ImportError:
    HAS_FIRE = False

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.table import Table
    from rich.panel import Panel
    from rich import print as rprint
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    # Create a fallback console with a print method
    class FallbackConsole:
        def print(self, *args, **kwargs):
            print(*args)
    
    console = FallbackConsole()
    def rprint(*args, **kwargs):
        print(*args)


class EnhancedLogger:
    """Enhanced logging with rich formatting"""
    
    def __init__(self, name: str = "MLOps"):
        self.name = name
        self.use_rich = HAS_RICH
    
    def info(self, message: str, **kwargs):
        if self.use_rich:
            console.print(f"ℹ️ [blue]{self.name}[/blue] | {message}", **kwargs)
        else:
            print(f"ℹ️ {self.name} | {message}")
    
    def success(self, message: str, **kwargs):
        if self.use_rich:
            console.print(f"✅ [green]{self.name}[/green] | {message}", **kwargs)
        else:
            print(f"✅ {self.name} | {message}")
    
    def warning(self, message: str, **kwargs):
        if self.use_rich:
            console.print(f"⚠️ [yellow]{self.name}[/yellow] | {message}", **kwargs)
        else:
            print(f"⚠️ {self.name} | {message}")
    
    def error(self, message: str, **kwargs):
        if self.use_rich:
            console.print(f"❌ [red]{self.name}[/red] | {message}", **kwargs)
        else:
            print(f"❌ {self.name} | {message}")
    
    def debug(self, *args, **kwargs):
        if HAS_ICECREAM:
            ic(*args)
        else:
            self.info(f"DEBUG: {args}")

class ProgressTracker:
    """Enhanced progress tracking with tqdm and rich"""
    
    def __init__(self, use_rich: bool = True):
        self.use_rich = use_rich and HAS_RICH
        self.use_tqdm = HAS_TQDM
    
    def track(self, iterable, description: str = "Processing", total: Optional[int] = None):
        """Track progress of an iterable"""
        if self.use_tqdm:
            return tqdm(iterable, desc=description, total=total)
        else:
            return iterable
    
    def progress_context(self, description: str = "Working..."):
        """Rich progress context manager"""
        if self.use_rich and HAS_RICH:
            # Only use Progress when Rich is available
            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
            from rich.console import Console
            if isinstance(console, Console):    
                return Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=console
                )
            else:
                # 필요시 새로운 Console instance 생성
                rich_console = Console()
                return Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description{task.description}]"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=rich_console
                )
        else:
            # Fallback context manager
            class DummyProgress:
                def __enter__(self):
                    print(f"🔄 {description}")
                    return self
                def __exit__(self, *args):
                    print("✅ Complete")
                def add_task(self, description, total=100):
                    return 0
                def update(self, task_id, advance=1):
                    pass
            return DummyProgress()
            
def enhanced_print(*args, **kwargs):
    """Enhanced print function with rich formatting"""
    if HAS_RICH:
        rprint(*args, **kwargs)
    else:
        print(*args, **kwargs)

# For type checking
if TYPE_CHECKING:
    from rich.table import Table

def create_table(title: str, headers: List[str], rows: List[List[str]]) -> Union[Table,str]:
    """Create a formatted table
    
    Args:
        title: The table title
        headers: List of column headers
        rows: List of rows, each containing a list of cell values
        
    Returns:
        Either a Rich Table object (if Rich is available) or a string representation
    """
    if HAS_RICH:
        from rich.table import Table
        table = Table(title=title)
        for header in headers:
            table.add_column(header)
        for row in rows:
            table.add_row(*row)
        return table
    else:
        # Fallback to simple text table
        lines = [title, "=" * len(title)]
        lines.append(" | ".join(headers))
        lines.append("-" * (len(" | ".join(headers))))
        for row in rows:
            lines.append(" | ".join(row))
        return "\n".join(lines)

def display_table(title: str, headers: List[str], rows: List[List[str]]):
    """Display a formatted table"""
    if HAS_RICH:
        table = create_table(title, headers, rows)
        console.print(table)
    else:
        print(create_table(title, headers, rows))

class MLOpsTools:
    """Collection of enhanced MLOps utility functions"""
    
    def __init__(self):
        self.logger = EnhancedLogger("MLOpsTools")
        self.progress = ProgressTracker()
    
    def debug_model_info(self, model: Any, data: Any = None):
        """Debug model information with enhanced output"""
        ic(type(model))
        ic(hasattr(model, 'predict'))
        ic(hasattr(model, 'fit'))
        
        if data is not None:
            ic(data.shape if hasattr(data, 'shape') else len(data))
        
        if hasattr(model, 'get_params'):
            ic(model.get_params())
    
    def debug_api_request(self, endpoint: str, data: Dict[str, Any], response: Dict[str, Any]):
        """Debug API request/response with enhanced formatting"""
        ic(endpoint)
        ic(data)
        ic(response)
        
        # Rich formatting if available
        if HAS_RICH:
            from rich.panel import Panel
            console.print(Panel(
                f"[bold]Endpoint:[/bold] {endpoint}\n"
                f"[bold]Request:[/bold] {data}\n"
                f"[bold]Response:[/bold] {response}",
                title="🔍 API Debug",
                border_style="blue"
            ))
    
    def process_with_progress(self, items: List[Any], func, description: str = "Processing"):
        """Process items with progress bar"""
        results = []
        for item in self.progress.track(items, description):
            result = func(item)
            results.append(result)
        return results
    
    def time_function(self, func, *args, **kwargs):
        """Time function execution with enhanced output"""
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        
        self.logger.info(f"Function {func.__name__} took {elapsed:.4f} seconds")
        ic(elapsed)
        
        return result, elapsed

def create_cli_from_class(cls, name: Optional[str] = None):
    """Create CLI interface from class using fire
    
    Args:
        cls: The class to create a CLI for
        name: Optional name for the CLI
        
    Returns:
        The result of fire.Fire or None if fire is not available
    """
    if not HAS_FIRE:
        print("❌ Fire not available. Install with: pip install fire")
        return None
    
    if name:
        import fire
        print(f"🔥 Starting {name} CLI...")

    if HAS_FIRE:
        import fire
        return fire.Fire(cls)
    return None

def create_cli_from_functions(**functions):
    """Create CLI interface from functions using fire"""
    if not HAS_FIRE:
        print("❌ Fire not available. Install with: pip install fire")
        return
    
    if HAS_FIRE:
        import fire
        print("🔥 Starting function CLI...")
        return fire.Fire(functions)

# Example usage functions for demonstration
def demo_enhanced_features():
    """Demonstrate enhanced features"""
    logger = EnhancedLogger("Demo")
    progress = ProgressTracker()
    
    logger.info("Starting enhanced features demo...")
    
    # Debug with icecream
    test_data = {"model": "RandomForest", "accuracy": 0.85}
    ic(test_data)
    
    # Progress bar demo
    items = list(range(100))
    results = []
    
    for item in progress.track(items, "Processing demo data"):
        time.sleep(0.01)  # Simulate work
        results.append(item * 2)
    
    logger.success(f"Processed {len(results)} items")
    
    # Table display
    display_table(
        "Model Results",
        ["Model", "Accuracy", "F1-Score"],
        [
            ["RandomForest", "0.85", "0.83"],
            ["LinearRegression", "0.72", "0.70"],
            ["NeuralNetwork", "0.88", "0.86"]
        ]
    )
    
    return results

class ExampleCLI:
    """Example CLI class using fire"""
    
    def __init__(self):
        self.logger = EnhancedLogger("CLI")
    
    def train(self, model_type: str = "random_forest", epochs: int = 10):
        """Train a model with given parameters"""
        self.logger.info(f"Training {model_type} for {epochs} epochs")
        ic(model_type, epochs)
        
        # Simulate training with progress
        progress = ProgressTracker()
        for epoch in progress.track(range(epochs), "Training"):
            time.sleep(0.1)  # Simulate training
        
        self.logger.success("Training completed!")
        return {"model_type": model_type, "epochs": epochs, "status": "completed"}
    
    def predict(self, input_text: str):
        """Make a prediction"""
        self.logger.info(f"Making prediction for: {input_text}")
        ic(input_text)
        
        # Simulate prediction
        prediction = len(input_text) % 10  # Dummy prediction
        self.logger.success(f"Prediction: {prediction}")
        
        return {"input": input_text, "prediction": prediction}
    
    def status(self):
        """Show system status"""
        self.logger.info("Checking system status...")
        
        display_table(
            "System Status",
            ["Component", "Status", "Details"],
            [
                ["API", "✅ Running", "Port 8000"],
                ["MLflow", "✅ Running", "Port 5000"],
                ["Database", "✅ Connected", "SQLite"],
                ["Models", "✅ Loaded", "10 available"]
            ]
        )
        
        return {"status": "all_systems_operational"}

# CLI functions for fire
def enhanced_train(model_type: str = "random_forest", data_path: str = "data/processed/movies_with_ratings.csv"):
    """Enhanced training function with progress tracking"""
    logger = EnhancedLogger("Training")
    progress = ProgressTracker()
    
    logger.info(f"Starting training with {model_type}")
    ic(model_type, data_path)
    
    # Simulate data loading with progress
    logger.info("Loading data...")
    for i in progress.track(range(100), "Loading data"):
        time.sleep(0.01)
    
    # Simulate training with progress
    logger.info("Training model...")
    for epoch in progress.track(range(50), "Training epochs"):
        time.sleep(0.02)
    
    logger.success("Training completed!")
    return {"model_type": model_type, "status": "completed"}

def enhanced_predict(title: str, year: int = 2020, runtime: int = 120, votes: int = 5000):
    """Enhanced prediction function with debug output"""
    logger = EnhancedLogger("Prediction")
    
    movie_data = {
        "title": title,
        "startYear": year,
        "runtimeMinutes": runtime,
        "numVotes": votes
    }
    
    ic(movie_data)
    logger.info(f"Predicting rating for: {title}")
    
    # Simulate prediction
    prediction = (year - 1900) / 100 + runtime / 100 + votes / 100000
    prediction = min(10.0, max(1.0, prediction))
    
    logger.success(f"Predicted rating: {prediction:.2f}/10")
    ic(prediction)
    
    return {"movie": movie_data, "predicted_rating": prediction}

def enhanced_docker_status():
    """Check Docker container status with enhanced output"""
    logger = EnhancedLogger("Docker")
    
    try:
        import subprocess
        result = subprocess.run(
            ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            logger.success("Docker containers status:")
            print(result.stdout)
        else:
            logger.error("Failed to check Docker status")
            
    except Exception as e:
        logger.error(f"Docker status check failed: {e}")
        ic(e)

# Global enhanced tools instance
tools = MLOpsTools()

# Convenience functions
def debug(*args):
    """Quick debug function"""
    ic(*args)

def log_info(message: str):
    """Quick info logging"""
    tools.logger.info(message)

def log_success(message: str):
    """Quick success logging"""
    tools.logger.success(message)

def log_error(message: str):
    """Quick error logging"""
    tools.logger.error(message)

def track_progress(iterable, description: str = "Processing"):
    """Quick progress tracking"""
    return tools.progress.track(iterable, description)

def get_package_version(package_name: str) -> str:
    """Get version of any installed package"""
    try:
        from importlib.metadata import version
        return version(package_name)
    except ImportError:
        # Python < 3.8 fallback
        try:
            import pkg_resources
            return pkg_resources.get_distribution(package_name).version
        except Exception:
            return "unknown"
        # Usage
        # prometheus_version = get_package_version('prometheus-client')
        # print(f"prometheus_client version: {prometheus_version}")

# CLI setup for fire
CLI_FUNCTIONS = {
    "train": enhanced_train,
    "predict": enhanced_predict,
    "demo": demo_enhanced_features,
    "docker_status": enhanced_docker_status,
    "cli_class": ExampleCLI
}

def main():
    """Main CLI entry point"""
    if HAS_FIRE:
        import fire
        print("🔥 MLOps Enhanced CLI")
        print("Available commands: train, predict, demo, docker_status, cli_class")
        fire.Fire(CLI_FUNCTIONS)
    else:
        print("❌ Fire not available. Install enhanced dependencies:")
        print("pip install -r requirements-enhanced.txt")

if __name__ == "__main__":
    main()