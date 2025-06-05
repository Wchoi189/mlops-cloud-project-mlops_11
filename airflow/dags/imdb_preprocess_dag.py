from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from pathlib import Path

# src 경로 추가
import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))

# IMDb 데이터 로더 임포트
from src.data.data_loader import IMDbDataLoader

# Airflow 작업 공간 절대 경로 설정
from pathlib import Path
import os

# 전처리 함수 정의
def run_preprocessing():
    project_root = Path(__file__).resolve().parents[2]  # 프로젝트 루트 경로
    data_dir = project_root / "data"
    print(f"데이터 디렉토리: {data_dir}")

    loader = IMDbDataLoader()
    loader.create_movie_dataset(
        sample_size=100000,
        save_path=str(data_dir / "processed" / "movies_with_ratings.csv")
    ) # size 필요한 만큼 조절

# DAG 정의
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),
    'retries': 1
}

with DAG(
    dag_id="imdb_preprocessing_pipeline",
    default_args=default_args,
    description="IMDb 데이터 전처리 DAG",
    schedule_interval=None,  # 필요 시 "@daily", "@weekly" 등으로 변경
    catchup=False,
    tags=["imdb", "preprocessing", "mlops"]
) as dag:

    preprocess_task = PythonOperator(
        task_id='run_imdb_preprocessing',
        python_callable=run_preprocessing
    )

    preprocess_task