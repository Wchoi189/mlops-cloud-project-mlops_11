"""
TMDB 데이터 수집 DAG
매일 자동으로 영화 데이터를 수집하고 처리하는 워크플로우
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
import sys
import os

# 프로젝트 경로 설정
sys.path.append('/opt/airflow/src')

# 기본 DAG 설정
default_args = {
    'owner': 'mlops-team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'catchup': False
}

# DAG 정의
dag = DAG(
    'tmdb_daily_collection',
    default_args=default_args,
    description='TMDB 일일 데이터 수집 워크플로우',
    schedule_interval='0 2 * * *',  # 매일 새벽 2시
    max_active_runs=1,
    tags=['tmdb', 'data-collection', 'daily'],
)

def collect_popular_movies(**context):
    """인기 영화 데이터 수집"""
    from data_processing.tmdb_api_connector import TMDBAPIConnector
    import json
    from pathlib import Path
    
    # API 커넥터 생성
    connector = TMDBAPIConnector()
    
    try:
        # 인기 영화 수집 (최신 5페이지)
        all_movies = []
        for page in range(1, 6):
            response = connector.get_popular_movies(page)
            if response and 'results' in response:
                all_movies.extend(response['results'])
        
        # 수집 통계
        collection_stats = {
            'collection_type': 'daily_popular',
            'collection_date': context['ds'],
            'total_collected': len(all_movies),
            'pages_processed': 5,
            'start_time': context['ts'],
            'dag_run_id': context['dag_run'].run_id
        }
        
        # 데이터 저장
        data_dir = Path('/opt/airflow/data/raw/movies/daily')
        data_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = data_dir / f"popular_movies_{context['ds_nodash']}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'movies': all_movies,
                'collection_info': collection_stats
            }, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✅ 인기 영화 {len(all_movies)}개 수집 완료")
        print(f"📁 저장 위치: {output_file}")
        
        # XCom에 통계 정보 저장 (다음 태스크에서 사용)
        return collection_stats
        
    except Exception as e:
        print(f"❌ 인기 영화 수집 실패: {e}")
        raise
    finally:
        connector.close()

def collect_trending_movies(**context):
    """트렌딩 영화 데이터 수집"""
    from data_processing.tmdb_api_connector import TMDBAPIConnector
    import json
    from pathlib import Path
    
    connector = TMDBAPIConnector()
    
    try:
        # 트렌딩 영화 수집
        trending_response = connector.get_trending_movies('day')
        trending_movies = trending_response.get('results', []) if trending_response else []
        
        collection_stats = {
            'collection_type': 'daily_trending',
            'collection_date': context['ds'],
            'total_collected': len(trending_movies),
            'time_window': 'day',
            'dag_run_id': context['dag_run'].run_id
        }
        
        # 데이터 저장
        data_dir = Path('/opt/airflow/data/raw/movies/trending')
        data_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = data_dir / f"trending_movies_{context['ds_nodash']}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'movies': trending_movies,
                'collection_info': collection_stats
            }, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✅ 트렌딩 영화 {len(trending_movies)}개 수집 완료")
        return collection_stats
        
    except Exception as e:
        print(f"❌ 트렌딩 영화 수집 실패: {e}")
        raise
    finally:
        connector.close()

def validate_collected_data(**context):
    """수집된 데이터 품질 검증"""
    from data_processing.quality_validator import DataQualityValidator
    import json
    from pathlib import Path
    
    # 이전 태스크에서 수집된 데이터 파일들 확인
    data_files = [
        f"/opt/airflow/data/raw/movies/daily/popular_movies_{context['ds_nodash']}.json",
        f"/opt/airflow/data/raw/movies/trending/trending_movies_{context['ds_nodash']}.json"
    ]
    
    validator = DataQualityValidator()
    validation_results = {
        'validation_date': context['ds'],
        'files_validated': [],
        'overall_quality_score': 0,
        'total_movies_validated': 0,
        'total_movies_passed': 0
    }
    
    all_movies = []
    
    for file_path in data_files:
        if Path(file_path).exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                movies = data.get('movies', [])
                all_movies.extend(movies)
                
                validation_results['files_validated'].append({
                    'file': file_path,
                    'movie_count': len(movies)
                })
    
    if all_movies:
        # 배치 검증 실행
        batch_results = validator.validate_batch_data(all_movies)
        
        validation_results.update({
            'total_movies_validated': batch_results['total_movies'],
            'total_movies_passed': batch_results['valid_movies'],
            'validation_rate': (batch_results['valid_movies'] / batch_results['total_movies'] * 100) if batch_results['total_movies'] > 0 else 0,
            'quality_distribution': batch_results['quality_distribution'],
            'common_issues': batch_results['common_issues']
        })
        
        # 검증 결과 저장
        report_dir = Path('/opt/airflow/data/raw/metadata/quality_reports')
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = report_dir / f"validation_report_{context['ds_nodash']}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(validation_results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✅ 데이터 검증 완료: {validation_results['validation_rate']:.1f}% 통과")
        print(f"📊 검증 보고서: {report_file}")
        
        # 검증 실패 시 알림
        if validation_results['validation_rate'] < 80:
            print(f"⚠️ 데이터 품질 경고: 검증 통과율이 {validation_results['validation_rate']:.1f}%로 낮습니다.")
        
        return validation_results
    
    else:
        raise ValueError("검증할 데이터가 없습니다.")

def generate_daily_summary(**context):
    """일일 수집 요약 생성"""
    task_instance = context['task_instance']
    
    # 이전 태스크들의 결과 수집
    popular_stats = task_instance.xcom_pull(task_ids='collect_popular_movies')
    trending_stats = task_instance.xcom_pull(task_ids='collect_trending_movies')
    validation_results = task_instance.xcom_pull(task_ids='validate_collected_data')
    
    # 일일 요약 생성
    daily_summary = {
        'summary_date': context['ds'],
        'dag_run_id': context['dag_run'].run_id,
        'collection_summary': {
            'popular_movies': popular_stats.get('total_collected', 0) if popular_stats else 0,
            'trending_movies': trending_stats.get('total_collected', 0) if trending_stats else 0,
            'total_collected': 0
        },
        'quality_summary': validation_results if validation_results else {},
        'execution_summary': {
            'start_time': context['dag_run'].start_date.isoformat() if context['dag_run'].start_date else None,
            'end_time': datetime.now().isoformat(),
            'duration_minutes': 0
        }
    }
    
    # 총 수집량 계산
    daily_summary['collection_summary']['total_collected'] = (
        daily_summary['collection_summary']['popular_movies'] +
        daily_summary['collection_summary']['trending_movies']
    )
    
    # 실행 시간 계산
    if context['dag_run'].start_date:
        duration = datetime.now() - context['dag_run'].start_date
        daily_summary['execution_summary']['duration_minutes'] = duration.total_seconds() / 60
    
    # 요약 저장
    summary_dir = Path('/opt/airflow/data/raw/metadata/daily_summaries')
    summary_dir.mkdir(parents=True, exist_ok=True)
    
    summary_file = summary_dir / f"daily_summary_{context['ds_nodash']}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(daily_summary, f, ensure_ascii=False, indent=2, default=str)
    
    # 콘솔 출력
    print("\n" + "="*50)
    print("📈 TMDB 일일 수집 요약")
    print("="*50)
    print(f"📅 수집 날짜: {context['ds']}")
    print(f"🎬 인기 영화: {daily_summary['collection_summary']['popular_movies']}개")
    print(f"🔥 트렌딩 영화: {daily_summary['collection_summary']['trending_movies']}개")
    print(f"📊 총 수집량: {daily_summary['collection_summary']['total_collected']}개")
    
    if validation_results:
        print(f"✅ 품질 검증: {validation_results.get('validation_rate', 0):.1f}% 통과")
    
    print(f"⏱️ 실행 시간: {daily_summary['execution_summary']['duration_minutes']:.1f}분")
    print(f"📁 요약 보고서: {summary_file}")
    print("="*50)
    
    return daily_summary

def cleanup_old_data(**context):
    """오래된 데이터 정리"""
    from pathlib import Path
    import os
    from datetime import datetime, timedelta
    
    # 30일 이상 된 파일 정리
    cutoff_date = datetime.now() - timedelta(days=30)
    
    cleanup_dirs = [
        '/opt/airflow/data/raw/movies/daily',
        '/opt/airflow/data/raw/movies/trending',
        '/opt/airflow/data/raw/metadata/quality_reports'
    ]
    
    cleaned_files = 0
    
    for dir_path in cleanup_dirs:
        dir_obj = Path(dir_path)
        if dir_obj.exists():
            for file_path in dir_obj.glob('*.json'):
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < cutoff_date:
                    try:
                        file_path.unlink()
                        cleaned_files += 1
                        print(f"정리됨: {file_path}")
                    except Exception as e:
                        print(f"정리 실패: {file_path} - {e}")
    
    print(f"✅ 정리 완료: {cleaned_files}개 파일 삭제")
    return {'cleaned_files': cleaned_files}

# 태스크 정의
collect_popular_task = PythonOperator(
    task_id='collect_popular_movies',
    python_callable=collect_popular_movies,
    dag=dag,
    doc_md="""
    ## 인기 영화 수집
    
    TMDB API에서 인기 영화 목록을 수집합니다.
    - 최신 5페이지 (약 100개 영화)
    - JSON 형태로 저장
    - 수집 메타데이터 포함
    """
)

collect_trending_task = PythonOperator(
    task_id='collect_trending_movies',
    python_callable=collect_trending_movies,
    dag=dag,
    doc_md="""
    ## 트렌딩 영화 수집
    
    당일 트렌딩 영화 목록을 수집합니다.
    - 일간 트렌딩 영화
    - 실시간 인기 반영
    """
)

validate_data_task = PythonOperator(
    task_id='validate_collected_data',
    python_callable=validate_collected_data,
    dag=dag,
    doc_md="""
    ## 데이터 품질 검증
    
    수집된 데이터의 품질을 검증합니다.
    - 필수 필드 확인
    - 데이터 타입 검증
    - 비즈니스 규칙 적용
    - 품질 리포트 생성
    """
)

generate_summary_task = PythonOperator(
    task_id='generate_daily_summary',
    python_callable=generate_daily_summary,
    dag=dag,
    doc_md="""
    ## 일일 요약 생성
    
    하루 전체 수집 작업의 요약을 생성합니다.
    - 수집 통계
    - 품질 지표
    - 실행 시간
    - 종합 보고서
    """
)

cleanup_task = PythonOperator(
    task_id='cleanup_old_data',
    python_callable=cleanup_old_data,
    dag=dag,
    doc_md="""
    ## 오래된 데이터 정리
    
    30일 이상 된 데이터 파일을 정리합니다.
    - 디스크 공간 확보
    - 성능 최적화
    """
)

# 태스크 의존성 설정
[collect_popular_task, collect_trending_task] >> validate_data_task >> generate_summary_task >> cleanup_task
