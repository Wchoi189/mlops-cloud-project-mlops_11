"""
icecream, tqdm, fire, rich를 사용한 향상된 유틸리티
더 나은 디버깅, 진행률 추적, CLI 인터페이스
"""

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# 향상된 라이브러리들
try:
    from icecream import ic, install as ic_install
    HAS_ICECREAM = True
except ImportError:
    HAS_ICECREAM = False
    # icecream이 없을 때 print로 대체
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
    # 대체 반복자
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
    console = None
    def rprint(*args, **kwargs):
        print(*args, **kwargs)

# 더 나은 디버깅을 위한 icecream 설정
if HAS_ICECREAM:
    ic_install()  # ic()를 어디서나 사용 가능하게 만들기
    ic.configureOutput(prefix='🐛 DEBUG | ')

class EnhancedLogger:
    """Rich 포맷팅을 사용한 향상된 로깅"""
    
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
    """tqdm과 rich를 사용한 향상된 진행률 추적"""
    
    def __init__(self, use_rich: bool = True):
        self.use_rich = use_rich and HAS_RICH
        self.use_tqdm = HAS_TQDM
    
    def track(self, iterable, description: str = "처리 중", total: Optional[int] = None):
        """반복 가능한 객체의 진행률 추적"""
        if self.use_tqdm:
            return tqdm(iterable, desc=description, total=total)
        else:
            return iterable
    
    def progress_context(self, description: str = "작업 중..."):
        """Rich 진행률 컨텍스트 매니저"""
        if self.use_rich:
            return Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            )
        else:
            # 대체 컨텍스트 매니저
            class DummyProgress:
                def __enter__(self):
                    print(f"🔄 {description}")
                    return self
                def __exit__(self, *args):
                    print("✅ 완료")
                def add_task(self, description, total=100):
                    return 0
                def update(self, task_id, advance=1):
                    pass
            return DummyProgress()

def enhanced_print(*args, **kwargs):
    """Rich 포맷팅을 사용한 향상된 print 함수"""
    if HAS_RICH:
        rprint(*args, **kwargs)
    else:
        print(*args, **kwargs)

def create_table(title: str, headers: List[str], rows: List[List[str]]) -> str:
    """포맷된 테이블 생성"""
    if HAS_RICH:
        table = Table(title=title)
        for header in headers:
            table.add_column(header)
        for row in rows:
            table.add_row(*row)
        return table
    else:
        # 간단한 텍스트 테이블로 대체
        lines = [title, "=" * len(title)]
        lines.append(" | ".join(headers))
        lines.append("-" * (len(" | ".join(headers))))
        for row in rows:
            lines.append(" | ".join(row))
        return "\n".join(lines)

def display_table(title: str, headers: List[str], rows: List[List[str]]):
    """포맷된 테이블 표시"""
    if HAS_RICH:
        table = create_table(title, headers, rows)
        console.print(table)
    else:
        print(create_table(title, headers, rows))

class MLOpsTools:
    """향상된 MLOps 유틸리티 함수 모음"""
    
    def __init__(self):
        self.logger = EnhancedLogger("MLOpsTools")
        self.progress = ProgressTracker()
    
    def debug_model_info(self, model: Any, data: Any = None):
        """향상된 출력으로 모델 정보 디버깅"""
        ic(type(model))
        ic(hasattr(model, 'predict'))
        ic(hasattr(model, 'fit'))
        
        if data is not None:
            ic(data.shape if hasattr(data, 'shape') else len(data))
        
        if hasattr(model, 'get_params'):
            ic(model.get_params())
    
    def debug_api_request(self, endpoint: str, data: Dict[str, Any], response: Dict[str, Any]):
        """향상된 포맷팅으로 API 요청/응답 디버깅"""
        ic(endpoint)
        ic(data)
        ic(response)
        
        # Rich 포맷팅 사용 가능시
        if HAS_RICH:
            console.print(Panel(
                f"[bold]엔드포인트:[/bold] {endpoint}\n"
                f"[bold]요청:[/bold] {data}\n"
                f"[bold]응답:[/bold] {response}",
                title="🔍 API 디버그",
                border_style="blue"
            ))
    
    def process_with_progress(self, items: List[Any], func, description: str = "처리 중"):
        """진행률 표시줄과 함께 항목 처리"""
        results = []
        for item in self.progress.track(items, description):
            result = func(item)```python
            results.append(result)
        return results
    
    def time_function(self, func, *args, **kwargs):
        """향상된 출력으로 함수 실행 시간 측정"""
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        
        self.logger.info(f"함수 {func.__name__}이(가) {elapsed:.4f}초 걸렸습니다")
        ic(elapsed)
        
        return result, elapsed

def create_cli_from_class(cls, name: str = None):
    """fire를 사용하여 클래스에서 CLI 인터페이스 생성"""
    if not HAS_FIRE:
        print("❌ Fire를 사용할 수 없습니다. 설치하세요: pip install fire")
        return
    
    if name:
        print(f"🔥 {name} CLI 시작 중...")
    
    return fire.Fire(cls)

def create_cli_from_functions(**functions):
    """fire를 사용하여 함수들에서 CLI 인터페이스 생성"""
    if not HAS_FIRE:
        print("❌ Fire를 사용할 수 없습니다. 설치하세요: pip install fire")
        return
    
    print("🔥 함수 CLI 시작 중...")
    return fire.Fire(functions)

# 데모용 예제 사용 함수들
def demo_enhanced_features():
    """향상된 기능들 데모"""
    logger = EnhancedLogger("데모")
    progress = ProgressTracker()
    
    logger.info("향상된 기능 데모 시작...")
    
    # icecream으로 디버깅
    test_data = {"model": "RandomForest", "accuracy": 0.85}
    ic(test_data)
    
    # 진행률 표시줄 데모
    items = list(range(100))
    results = []
    
    for item in progress.track(items, "데모 데이터 처리"):
        time.sleep(0.01)  # 작업 시뮬레이션
        results.append(item * 2)
    
    logger.success(f"{len(results)}개 항목을 처리했습니다")
    
    # 테이블 표시
    display_table(
        "모델 결과",
        ["모델", "정확도", "F1-점수"],
        [
            ["RandomForest", "0.85", "0.83"],
            ["LinearRegression", "0.72", "0.70"],
            ["NeuralNetwork", "0.88", "0.86"]
        ]
    )
    
    return results

class ExampleCLI:
    """fire를 사용한 예제 CLI 클래스"""
    
    def __init__(self):
        self.logger = EnhancedLogger("CLI")
    
    def train(self, model_type: str = "random_forest", epochs: int = 10):
        """주어진 매개변수로 모델 훈련"""
        self.logger.info(f"{model_type}을(를) {epochs} 에포크 동안 훈련")
        ic(model_type, epochs)
        
        # 진행률과 함께 훈련 시뮬레이션
        progress = ProgressTracker()
        for epoch in progress.track(range(epochs), "훈련"):
            time.sleep(0.1)  # 훈련 시뮬레이션
        
        self.logger.success("훈련 완료!")
        return {"model_type": model_type, "epochs": epochs, "status": "completed"}
    
    def predict(self, input_text: str):
        """예측 수행"""
        self.logger.info(f"예측 수행 중: {input_text}")
        ic(input_text)
        
        # 예측 시뮬레이션
        prediction = len(input_text) % 10  # 더미 예측
        self.logger.success(f"예측: {prediction}")
        
        return {"input": input_text, "prediction": prediction}
    
    def status(self):
        """시스템 상태 표시"""
        self.logger.info("시스템 상태 확인 중...")
        
        display_table(
            "시스템 상태",
            ["구성요소", "상태", "세부사항"],
            [
                ["API", "✅ 실행 중", "포트 8000"],
                ["MLflow", "✅ 실행 중", "포트 5000"],
                ["데이터베이스", "✅ 연결됨", "SQLite"],
                ["모델", "✅ 로드됨", "10개 사용 가능"]
            ]
        )
        
        return {"status": "all_systems_operational"}

# fire용 CLI 함수들
def enhanced_train(model_type: str = "random_forest", data_path: str = "data/processed/movies_with_ratings.csv"):
    """진행률 추적이 포함된 향상된 훈련 함수"""
    logger = EnhancedLogger("훈련")
    progress = ProgressTracker()
    
    logger.info(f"{model_type}로 훈련 시작")
    ic(model_type, data_path)
    
    # 진행률과 함께 데이터 로딩 시뮬레이션
    logger.info("데이터 로딩 중...")
    for i in progress.track(range(100), "데이터 로딩"):
        time.sleep(0.01)
    
    # 진행률과 함께 훈련 시뮬레이션
    logger.info("모델 훈련 중...")
    for epoch in progress.track(range(50), "훈련 에포크"):
        time.sleep(0.02)
    
    logger.success("훈련 완료!")
    return {"model_type": model_type, "status": "completed"}

def enhanced_predict(title: str, year: int = 2020, runtime: int = 120, votes: int = 5000):
    """디버그 출력이 포함된 향상된 예측 함수"""
    logger = EnhancedLogger("예측")
    
    movie_data = {
        "title": title,
        "startYear": year,
        "runtimeMinutes": runtime,
        "numVotes": votes
    }
    
    ic(movie_data)
    logger.info(f"영화 평점 예측 중: {title}")
    
    # 예측 시뮬레이션
    prediction = (year - 1900) / 100 + runtime / 100 + votes / 100000
    prediction = min(10.0, max(1.0, prediction))
    
    logger.success(f"예측된 평점: {prediction:.2f}/10")
    ic(prediction)
    
    return {"movie": movie_data, "predicted_rating": prediction}

def enhanced_docker_status():
    """향상된 출력으로 Docker 컨테이너 상태 확인"""
    logger = EnhancedLogger("Docker")
    
    try:
        import subprocess
        result = subprocess.run(
            ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            logger.success("Docker 컨테이너 상태:")
            print(result.stdout)
        else:
            logger.error("Docker 상태 확인 실패")
            
    except Exception as e:
        logger.error(f"Docker 상태 확인 실패: {e}")
        ic(e)

def enhanced_system_info():
    """시스템 정보 표시"""
    logger = EnhancedLogger("시스템")
    
    try:
        import psutil
        
        # CPU 정보
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # 메모리 정보
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_total = memory.total / (1024**3)  # GB
        memory_used = memory.used / (1024**3)   # GB
        
        # 디스크 정보
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_total = disk.total / (1024**3)  # GB
        disk_used = disk.used / (1024**3)    # GB
        
        display_table(
            "시스템 리소스 정보",
            ["리소스", "사용률", "세부사항"],
            [
                ["CPU", f"{cpu_percent:.1f}%", f"{cpu_count}개 코어"],
                ["메모리", f"{memory_percent:.1f}%", f"{memory_used:.1f}GB / {memory_total:.1f}GB"],
                ["디스크", f"{disk_percent:.1f}%", f"{disk_used:.1f}GB / {disk_total:.1f}GB"]
            ]
        )
        
        ic(cpu_percent, memory_percent, disk_percent)
        
    except ImportError:
        logger.warning("psutil이 설치되지 않았습니다. 기본 정보만 표시합니다.")
        display_table(
            "기본 시스템 정보",
            ["항목", "값"],
            [
                ["Python 버전", sys.version.split()[0]],
                ["플랫폼", sys.platform],
                ["작업 디렉토리", os.getcwd()]
            ]
        )
    except Exception as e:
        logger.error(f"시스템 정보 수집 실패: {e}")
        ic(e)

def enhanced_model_benchmark():
    """모델 성능 벤치마크"""
    logger = EnhancedLogger("벤치마크")
    progress = ProgressTracker()
    
    logger.info("모델 성능 벤치마크 시작...")
    
    # 가상의 모델들과 성능 데이터
    models = ["RandomForest", "LinearRegression", "XGBoost", "NeuralNetwork"]
    results = []
    
    for model in progress.track(models, "모델 벤치마킹"):
        # 벤치마크 시뮬레이션
        time.sleep(0.5)
        
        # 가상의 성능 메트릭
        import random
        accuracy = random.uniform(0.7, 0.95)
        training_time = random.uniform(10, 300)
        inference_time = random.uniform(0.001, 0.1)
        
        results.append([
            model,
            f"{accuracy:.3f}",
            f"{training_time:.1f}초",
            f"{inference_time:.3f}초"
        ])
        
        ic(model, accuracy, training_time, inference_time)
    
    display_table(
        "모델 성능 벤치마크 결과",
        ["모델", "정확도", "훈련 시간", "추론 시간"],
        results
    )
    
    logger.success("벤치마크 완료!")
    return results

# 전역 향상된 도구 인스턴스
tools = MLOpsTools()

# 편의 함수들
def debug(*args):
    """빠른 디버그 함수"""
    ic(*args)

def log_info(message: str):
    """빠른 정보 로깅"""
    tools.logger.info(message)

def log_success(message: str):
    """빠른 성공 로깅"""
    tools.logger.success(message)

def log_error(message: str):
    """빠른 에러 로깅"""
    tools.logger.error(message)

def log_warning(message: str):
    """빠른 경고 로깅"""
    tools.logger.warning(message)

def track_progress(iterable, description: str = "처리 중"):
    """빠른 진행률 추적"""
    return tools.progress.track(iterable, description)

def time_it(func, *args, **kwargs):
    """함수 실행 시간 측정"""
    return tools.time_function(func, *args, **kwargs)

# fire용 CLI 설정
CLI_FUNCTIONS = {
    "train": enhanced_train,
    "predict": enhanced_predict,
    "demo": demo_enhanced_features,
    "docker_status": enhanced_docker_status,
    "system_info": enhanced_system_info,
    "benchmark": enhanced_model_benchmark,
    "cli_class": ExampleCLI
}

def show_help():
    """사용 가능한 명령어 도움말 표시"""
    logger = EnhancedLogger("도움말")
    
    logger.info("MLOps 향상된 CLI 도구")
    
    display_table(
        "사용 가능한 명령어",
        ["명령어", "설명", "예제"],
        [
            ["train", "모델 훈련", "python enhanced_utils.py train --model_type=xgboost"],
            ["predict", "예측 수행", "python enhanced_utils.py predict --title='영화제목'"],
            ["demo", "기능 데모", "python enhanced_utils.py demo"],
            ["docker_status", "Docker 상태", "python enhanced_utils.py docker_status"],
            ["system_info", "시스템 정보", "python enhanced_utils.py system_info"],
            ["benchmark", "모델 벤치마크", "python enhanced_utils.py benchmark"],
            ["cli_class", "CLI 클래스", "python enhanced_utils.py cli_class train"]
        ]
    )

def main():
    """메인 CLI 진입점"""
    if HAS_FIRE:
        print("🔥 MLOps 향상된 CLI")
        print("사용 가능한 명령어: train, predict, demo, docker_status, system_info, benchmark, cli_class")
        print("도움말: python enhanced_utils.py --help")
        
        # 도움말 함수 추가
        CLI_FUNCTIONS["help"] = show_help
        
        fire.Fire(CLI_FUNCTIONS)
    else:
        print("❌ Fire를 사용할 수 없습니다. 향상된 의존성을 설치하세요:")
        print("pip install -r requirements-enhanced.txt")
        print("\n필요한 패키지:")
        print("- fire")
        print("- icecream")
        print("- tqdm")
        print("- rich")

# 추가 유틸리티 함수들
def create_progress_bar(total: int, description: str = "진행 중"):
    """사용자 정의 진행률 표시줄 생성"""
    if HAS_RICH:
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        )
    else:
        return None

def format_time(seconds: float) -> str:
    """시간을 읽기 쉬운 형식으로 포맷"""
    if seconds < 60:
        return f"{seconds:.2f}초"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}분"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}시간"

def format_size(bytes_size: int) -> str:
    """바이트 크기를 읽기 쉬운 형식으로 포맷"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f}PB"

def enhanced_file_info(file_path: str):
    """파일 정보를 향상된 형식으로 표시"""
    logger = EnhancedLogger("파일정보")
    
    try:
        path = Path(file_path)
        if not path.exists():
            logger.error(f"파일을 찾을 수 없습니다: {file_path}")
            return
        
        stat = path.stat()
        size = stat.st_size
        modified = time.ctime(stat.st_mtime)
        
        display_table(
            f"파일 정보: {path.name}",
            ["속성", "값"],
            [
                ["경로", str(path.absolute())],
                ["크기", format_size(size)],
                ["수정일", modified],
                ["타입", "디렉토리" if path.is_dir() else "파일"],
                ["확장자", path.suffix if path.suffix else "없음"]
            ]
        )
        
        ic(file_path, size, modified)
        
    except Exception as e:
        logger.error(f"파일 정보 수집 실패: {e}")
        ic(e)

def enhanced_env_info():
    """환경 변수 정보 표시"""
    logger = EnhancedLogger("환경정보")
    
    important_vars = [
        "PYTHONPATH", "PATH", "MODEL_PATH", "DATA_PATH", 
        "MLFLOW_TRACKING_URI", "LOG_LEVEL"
    ]
    
    env_data = []
    for var in important_vars:
        value = os.environ.get(var, "설정되지 않음")
        # 긴 값은 줄임
        if len(value) > 50:
            value = value[:47] + "..."
        env_data.append([var, value])
    
    display_table(
        "중요한 환경 변수",
        ["변수", "값"],
        env_data
    )
    
    logger.info(f"총 {len(os.environ)}개의 환경 변수가 설정되어 있습니다")

def enhanced_dependency_check():
    """의존성 패키지 확인"""
    logger = EnhancedLogger("의존성체크")
    
    required_packages = [
        "pandas", "numpy", "scikit-learn", "fastapi", 
        "uvicorn", "mlflow", "joblib", "matplotlib", "seaborn"
    ]
    
    optional_packages = [
        "icecream", "tqdm", "fire", "rich", "psutil"
    ]
    
    def check_package(package_name):
        try:
            __import__(package_name)
            return "✅ 설치됨"
        except ImportError:
            return "❌ 누락"
    
    # 필수 패키지 확인
    required_data = []
    for pkg in required_packages:
        status = check_package(pkg)
        required_data.append([pkg, status])
    
    display_table("필수 패키지", ["패키지", "상태"], required_data)
    
    # 선택적 패키지 확인
    optional_data = []
    for pkg in optional_packages:
        status = check_package(pkg)
        optional_data.append([pkg, status])
    
    display_table("선택적 패키지 (향상된 기능)", ["패키지", "상태"], optional_data)

# CLI에 새로운 함수들 추가
CLI_FUNCTIONS.update({
    "file_info": enhanced_file_info,
    "env_info": enhanced_env_info,
    "dep_check": enhanced_dependency_check
})

# 컨텍스트 매니저들
class TimedOperation:
    """시간 측정 컨텍스트 매니저"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.logger = EnhancedLogger("타이머")
        self.start_time = None
    
    def __enter__(self):
        self.logger.info(f"{self.operation_name} 시작...")
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        if exc_type is None:
            self.logger.success(f"{self.operation_name} 완료 ({format_time(elapsed)})")
        else:
            self.logger.error(f"{self.operation_name} 실패 ({format_time(elapsed)})")
        ic(self.operation_name, elapsed)

class LoggedOperation:
    """로깅이 포함된 작업 컨텍스트 매니저"""
    
    def __init__(self, operation_name: str, logger_name: str = "작업"):
        self.operation_name = operation_name
        self.logger = EnhancedLogger(logger_name)
    
    def __enter__(self):
        self.logger.info(f"{self.operation_name} 시작...")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.logger.success(f"{self.operation_name} 성공적으로 완료")
        else:
            self.logger.error(f"{self.operation_name} 실패: {exc_val}")
            ic(exc_type, exc_val)

# 사용 예제 함수
def example_usage():
    """향상된 유틸리티 사용 예제"""
    logger = EnhancedLogger("예제")
    
    logger.info("향상된 유틸리티 사용 예제 시작")
    
    # 시간 측정 예제
    with TimedOperation("데이터 처리"):
        time.sleep(1)  # 작업 시뮬레이션
    
    # 로깅된 작업 예제
    with LoggedOperation("모델 로딩", "모델"):
        time.sleep(0.5)  # 작업 시뮬레이션
    
    # 진행률 추적 예제
    items = list(range(50))
    results = []
    
    for item in track_progress(items, "항목 처리"):
        time.sleep(0.02)
        results.append(item ** 2)
    
    logger.success(f"총 {len(results)}개 항목 처리 완료")
    
    return results

# CLI에 예제 함수 추가
CLI_FUNCTIONS["example"] = example_usage

if __name__ == "__main__":
    main()
