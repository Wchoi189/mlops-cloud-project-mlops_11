# Import built-in logging first to avoid conflicts
import logging as builtin_logging
import os
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

# Enhanced libraries with proper error handling
try:
    from icecream import ic
    from icecream import install as ic_install

    HAS_ICECREAM = True
    # Setup icecream for better debugging
    if HAS_ICECREAM:
        ic_install()  # Make ic() available everywhere
        ic.configureOutput(prefix="🐛 DEBUG | ")
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
    from rich import print as rprint
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
    )
    from rich.table import Table

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
    """Enhanced logging with rich formatting - uses builtin_logging to avoid conflicts"""

    def __init__(self, name: str = "MLOps"):
        self.name = name
        self.use_rich = HAS_RICH
        # Use builtin_logging explicitly
        self.logger = builtin_logging.getLogger(name)

    def info(self, message: str, **kwargs):
        if self.use_rich:
            console.print(f"ℹ️ [blue]{self.name}[/blue] | {message}", **kwargs)
        else:
            print(f"ℹ️ {self.name} | {message}")
        self.logger.info(message)

    def success(self, message: str, **kwargs):
        if self.use_rich:
            console.print(f"✅ [green]{self.name}[/green] | {message}", **kwargs)
        else:
            print(f"✅ {self.name} | {message}")
        self.logger.info(f"SUCCESS: {message}")

    def warning(self, message: str, **kwargs):
        if self.use_rich:
            console.print(f"⚠️ [yellow]{self.name}[/yellow] | {message}", **kwargs)
        else:
            print(f"⚠️ {self.name} | {message}")
        self.logger.warning(message)

    def error(self, message: str, **kwargs):
        if self.use_rich:
            console.print(f"❌ [red]{self.name}[/red] | {message}", **kwargs)
        else:
            print(f"❌ {self.name} | {message}")
        self.logger.error(message)

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

    def track(
        self, iterable, description: str = "Processing", total: Optional[int] = None
    ):
        """Track progress of an iterable"""
        if self.use_tqdm:
            return tqdm(iterable, desc=description, total=total)
        else:
            return iterable

    def progress_context(self, description: str = "Working..."):
        """Rich progress context manager"""
        if self.use_rich and HAS_RICH:
            # Only use Progress when Rich is available
            from rich.console import Console
            from rich.progress import (
                BarColumn,
                Progress,
                SpinnerColumn,
                TaskProgressColumn,
                TextColumn,
            )

            if isinstance(console, Console):
                return Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=console,
                )
            else:
                # Create new Console instance if needed
                rich_console = Console()
                return Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=rich_console,
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


def create_table(
    title: str, headers: List[str], rows: List[List[str]]
) -> Union["Table", str]:
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
        ic(hasattr(model, "predict"))
        ic(hasattr(model, "fit"))

        if data is not None:
            ic(data.shape if hasattr(data, "shape") else len(data))

        if hasattr(model, "get_params"):
            ic(model.get_params())

    def debug_api_request(
        self, endpoint: str, data: Dict[str, Any], response: Dict[str, Any]
    ):
        """Debug API request/response with enhanced formatting"""
        ic(endpoint)
        ic(data)
        ic(response)

        # Rich formatting if available
        if HAS_RICH:
            from rich.panel import Panel

            console.print(
                Panel(
                    f"[bold]Endpoint:[/bold] {endpoint}\n"
                    f"[bold]Request:[/bold] {data}\n"
                    f"[bold]Response:[/bold] {response}",
                    title="🔍 API Debug",
                    border_style="blue",
                )
            )

    def process_with_progress(
        self, items: List[Any], func, description: str = "Processing"
    ):
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


def demo_enhanced_features():
    """Demonstrate enhanced features - safe version"""
    logger = EnhancedLogger("Demo")
    progress = ProgressTracker()

    logger.info("Starting enhanced features demo...")

    # Debug with icecream
    test_data = {"model": "RandomForest", "accuracy": 0.85}
    ic(test_data)

    # Simple progress demo without external dependencies
    items = list(range(10))  # Smaller range for CI
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
            ["NeuralNetwork", "0.88", "0.86"],
        ],
    )

    # Show available features
    features_info = {
        "icecream": HAS_ICECREAM,
        "tqdm": HAS_TQDM,
        "rich": HAS_RICH,
        "fire": HAS_FIRE,
    }

    logger.info("Available enhanced features:")
    for feature, available in features_info.items():
        status = "✅ Available" if available else "❌ Not installed"
        logger.info(f"  {feature}: {status}")

    return results


# Convenience functions
def debug(*args):
    """Quick debug function"""
    ic(*args)


def log_info(message: str):
    """Quick info logging"""
    logger = EnhancedLogger("Utils")
    logger.info(message)


def log_success(message: str):
    """Quick success logging"""
    logger = EnhancedLogger("Utils")
    logger.success(message)


def log_error(message: str):
    """Quick error logging"""
    logger = EnhancedLogger("Utils")
    logger.error(message)


def track_progress(iterable, description: str = "Processing"):
    """Quick progress tracking"""
    tracker = ProgressTracker()
    return tracker.track(iterable, description)


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


def test_imports():
    """Test all imports to ensure no conflicts"""
    print("🧪 Testing imports...")

    # Test built-in modules
    try:
        import logging

        print("✅ Built-in logging module works")
    except Exception as e:
        print(f"❌ Built-in logging failed: {e}")

    # Test enhanced features
    features = {
        "icecream": HAS_ICECREAM,
        "tqdm": HAS_TQDM,
        "rich": HAS_RICH,
        "fire": HAS_FIRE,
    }

    for name, available in features.items():
        status = "✅" if available else "⚠️"
        print(f"{status} {name}: {available}")

    return True


# Global enhanced tools instance
tools = MLOpsTools()


def main():
    """Main CLI entry point - safe for CI/CD"""
    print("🎬 MLOps Enhanced Utilities (CI/CD Safe)")
    print("=" * 50)

    # Test imports first
    test_imports()

    # Run demo
    print("\n🚀 Running demo...")
    try:
        results = demo_enhanced_features()
        print(f"✅ Demo completed successfully! {len(results)} items processed")
    except Exception as e:
        print(f"⚠️ Demo completed with warnings: {e}")

    # CLI functionality
    if HAS_FIRE and len(sys.argv) > 1:
        import fire

        fire.Fire({"demo": demo_enhanced_features, "test": test_imports})
    else:
        print("\n💡 Available functions:")
        print("  demo() - Run enhanced features demo")
        print("  test_imports() - Test import compatibility")


if __name__ == "__main__":
    main()
