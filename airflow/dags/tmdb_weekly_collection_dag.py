"""
TMDB 주간 종합 수집 DAG
주간 단위로 장르별, 평점별 영화 데이터를 종합적으로 수집
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago
import sys

sys.path.append('/opt/airflow/src')

default_args = {
    'owner': 'mlops-team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
    'catchup': False
}

dag = DAG(
    'tmdb_weekly_comprehensive',
    default_args=default_args,
    description='TMDB 주간 종합 데이터 수집',
    schedule_interval='0 3 * * 0',  # 매주 일요일 새벽 3시
    max_active_runs=1,
    tags=['tmdb', 'data-collection', 'weekly', 'comprehensive'],
)

# 주요 장르 정의
MAJOR_GENRES = {
    28: "액션",
    35: "코미디", 
    18: "드라마",
    27: "공포",
    10749: "로맨스",
    878: "SF",
    53: "스릴러",
    16: "애니메이션"
}

def collect_genre_movies(genre_id, genre_name, **context):
    """장르별 영화 수집"""
    from data_processing.tmdb_api_connector import TMDBAPIConnector
    import json
    from pathlib import Path
    
    connector = TMDBAPIConnector()
    
    try:
        # 장르별 영화 수집 (15페이지)
        all_movies = []
        for page in range(1, 16):
            response = connector.get_movies_by_genre(genre_id, page)
            if response and 'results' in response:
                all_movies.extend(response['results'])
            else:
                break
        
        # 중복 제거
        unique_movies = []
        seen_ids = set()
        for movie in all_movies:
            if movie.get('id') not in seen_ids:
                unique_movies.append(movie)
                seen_ids.add(movie.get('id'))
        
        collection_stats = {
            'collection_type': 'weekly_genre',
            'genre_id': genre_id,
            'genre_name': genre_name,
            'collection_date': context['ds'],
            'total_collected': len(unique_movies),
            'pages_processed': 15,
            'week_number': datetime.strptime(context['ds'], '%Y-%m-%d').isocalendar()[1]
        }
        
        # 데이터 저장
        data_dir = Path('/opt/airflow/data/raw/movies/genre')
        data_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = data_dir / f"{genre_name.lower()}_{context['ds_nodash']}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'movies': unique_movies,
                'collection_info': collection_stats
            }, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✅ {genre_name} 장르 영화 {len(unique_movies)}개 수집 완료")
        return collection_stats
        
    except Exception as e:
        print(f"❌ {genre_name} 장르 수집 실패: {e}")
        raise
    finally:
        connector.close()

def collect_top_rated_movies(**context):
    """평점 높은 영화 수집"""
    from data_processing.tmdb_api_connector import TMDBAPIConnector
    import json
    from pathlib import Path
    
    connector = TMDBAPIConnector()
    
    try:
        # 평점 높은 영화 수집
        all_movies = []
        for page in range(1, 21):  # 20페이지
            response = connector.get_top_rated_movies(page)
            if response and 'results' in response:
                # 평점 7.5 이상만 필터링
                high_rated = [m for m in response['results'] if m.get('vote_average', 0) >= 7.5]
                all_movies.extend(high_rated)
            else:
                break
        
        collection_stats = {
            'collection_type': 'weekly_top_rated',
            'collection_date': context['ds'],
            'total_collected': len(all_movies),
            'min_rating': 7.5,
            'pages_processed': 20
        }
        
        # 데이터 저장
        data_dir = Path('/opt/airflow/data/raw/movies/weekly')
        data_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = data_dir / f"top_rated_{context['ds_nodash']}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'movies': all_movies,
                'collection_info': collection_stats
            }, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✅ 평점 높은 영화 {len(all_movies)}개 수집 완료")
        return collection_stats
        
    except Exception as e:
        print(f"❌ 평점 높은 영화 수집 실패: {e}")
        raise
    finally:
        connector.close()

def consolidate_weekly_data(**context):
    """주간 수집 데이터 통합"""
    import json
    from pathlib import Path
    
    # 모든 주간 수집 파일 통합
    data_sources = [
        ('/opt/airflow/data/raw/movies/genre', '장르별'),
        ('/opt/airflow/data/raw/movies/weekly', '평점별')
    ]
    
    all_movies = []
    collection_summary = {
        'consolidation_date': context['ds'],
        'week_number': datetime.strptime(context['ds'], '%Y-%m-%d').isocalendar()[1],
        'sources_processed': [],
        'total_unique_movies': 0,
        'by_category': {}
    }
    
    seen_ids = set()
    
    for data_dir, category in data_sources:
        data_path = Path(data_dir)
        if data_path.exists():
            category_count = 0
            for file_path in data_path.glob(f"*{context['ds_nodash']}.json"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    movies = data.get('movies', [])
                    
                    # 중복 제거하면서 추가
                    for movie in movies:
                        if movie.get('id') not in seen_ids:
                            all_movies.append(movie)
                            seen_ids.add(movie.get('id'))
                            category_count += 1
                
                collection_summary['sources_processed'].append(str(file_path))
            
            collection_summary['by_category'][category] = category_count
    
    collection_summary['total_unique_movies'] = len(all_movies)
    
    # 통합 데이터 저장
    consolidated_dir = Path('/opt/airflow/data/processed/weekly')
    consolidated_dir.mkdir(parents=True, exist_ok=True)
    
    week_number = collection_summary['week_number']
    output_file = consolidated_dir / f"consolidated_week_{week_number}_{context['ds_nodash']}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'movies': all_movies,
            'consolidation_info': collection_summary
        }, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📊 주간 데이터 통합 완료")
    print(f"🎬 총 고유 영화: {len(all_movies)}개")
    for category, count in collection_summary['by_category'].items():
        print(f"  {category}: {count}개")
    print(f"📁 통합 파일: {output_file}")
    
    return collection_summary

def generate_weekly_report(**context):
    """주간 리포트 생성"""
    import json
    from pathlib import Path
    
    # 통합 데이터 로드
    week_number = datetime.strptime(context['ds'], '%Y-%m-%d').isocalendar()[1]
    consolidated_file = Path(f'/opt/airflow/data/processed/weekly/consolidated_week_{week_number}_{context["ds_nodash"]}.json')
    
    if not consolidated_file.exists():
        raise FileNotFoundError(f"통합 파일을 찾을 수 없습니다: {consolidated_file}")
    
    with open(consolidated_file, 'r', encoding='utf-8') as f:
        consolidated_data = json.load(f)
    
    movies = consolidated_data.get('movies', [])
    consolidation_info = consolidated_data.get('consolidation_info', {})
    
    # 분석 수행
    def analyze_genre_distribution(movies):
        genre_counts = {}
        for movie in movies:
            genres = movie.get('genre_ids', [])
            for genre_id in genres:
                genre_counts[genre_id] = genre_counts.get(genre_id, 0) + 1
        return dict(sorted(genre_counts.items(), key=lambda x: x[1], reverse=True))
    
    def analyze_rating_distribution(movies):
        rating_ranges = {
            '9.0-10.0': 0, '8.0-8.9': 0, '7.0-7.9': 0,
            '6.0-6.9': 0, '5.0-5.9': 0, '0.0-4.9': 0
        }
        
        for movie in movies:
            rating = movie.get('vote_average', 0)
            if rating >= 9.0:
                rating_ranges['9.0-10.0'] += 1
            elif rating >= 8.0:
                rating_ranges['8.0-8.9'] += 1
            elif rating >= 7.0:
                rating_ranges['7.0-7.9'] += 1
            elif rating >= 6.0:
                rating_ranges['6.0-6.9'] += 1
            elif rating >= 5.0:
                rating_ranges['5.0-5.9'] += 1
            else:
                rating_ranges['0.0-4.9'] += 1
        
        return rating_ranges
    
    # 리포트 생성
    report = {
        'report_type': 'weekly',
        'week_number': week_number,
        'generation_time': datetime.now().isoformat(),
        'data_summary': consolidation_info,
        'analysis': {
            'genre_distribution': analyze_genre_distribution(movies),
            'rating_distribution': analyze_rating_distribution(movies),
            'top_movies': sorted(movies, key=lambda x: x.get('popularity', 0), reverse=True)[:10]
        }
    }
    
    # 리포트 저장
    report_dir = Path('/opt/airflow/data/raw/metadata/weekly_reports')
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = report_dir / f"weekly_report_W{week_number}_{context['ds_nodash']}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📋 주간 리포트 생성 완료")
    print(f"📁 리포트 파일: {report_file}")
    
    return report

# 시작 태스크
start_task = DummyOperator(
    task_id='start_weekly_collection',
    dag=dag
)

# 장르별 수집 태스크들
genre_tasks = []
for genre_id, genre_name in MAJOR_GENRES.items():
    task = PythonOperator(
        task_id=f'collect_{genre_name.lower()}_movies',
        python_callable=collect_genre_movies,
        op_kwargs={'genre_id': genre_id, 'genre_name': genre_name},
        dag=dag
    )
    genre_tasks.append(task)

# 평점 높은 영화 수집 태스크
top_rated_task = PythonOperator(
    task_id='collect_top_rated_movies',
    python_callable=collect_top_rated_movies,
    dag=dag
)

# 데이터 통합 태스크
consolidate_task = PythonOperator(
    task_id='consolidate_weekly_data',
    python_callable=consolidate_weekly_data,
    dag=dag
)

# 리포트 생성 태스크
report_task = PythonOperator(
    task_id='generate_weekly_report',
    python_callable=generate_weekly_report,
    dag=dag
)

# 완료 태스크
end_task = DummyOperator(
    task_id='end_weekly_collection',
    dag=dag
)

# 태스크 의존성 설정
start_task >> [*genre_tasks, top_rated_task] >> consolidate_task >> report_task >> end_task
