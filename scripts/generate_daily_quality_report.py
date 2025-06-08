# scripts/generate_daily_quality_report.py
#!/usr/bin/env python3
"""
일간 데이터 품질 리포트 자동 생성 스크립트
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_processing.quality_reporter import QualityReporter

def main():
    parser = argparse.ArgumentParser(description='일간 데이터 품질 리포트 생성')
    parser.add_argument('--date', help='리포트 날짜 (YYYYMMDD), 기본값: 어제')
    parser.add_argument('--dashboard', action='store_true', help='대시보드 데이터도 함께 생성')
    parser.add_argument('--weekly', action='store_true', help='주간 요약도 함께 생성')
    
    args = parser.parse_args()
    
    # 날짜 설정
    if args.date:
        report_date = args.date
    else:
        # 어제 날짜 (보통 새벽에 실행)
        yesterday = datetime.now() - timedelta(days=1)
        report_date = yesterday.strftime('%Y%m%d')
    
    print(f"일간 품질 리포트 생성 중... (날짜: {report_date})")
    
    try:
        reporter = QualityReporter()
        
        # 일간 리포트 생성
        report = reporter.generate_daily_report(report_date)
        
        if report.get('status') == 'no_data':
            print(f"경고: {report_date} 날짜의 데이터를 찾을 수 없습니다.")
            return
        elif report.get('status') == 'no_movies':
            print(f"경고: {report_date} 날짜에 영화 데이터가 없습니다.")
            return
        
        # 리포트 요약 출력
        print("\n=== 일간 품질 리포트 요약 ===")
        print(f"분석된 영화 수: {report['data_summary']['total_movies_analyzed']}")
        print(f"전체 품질 점수: {report['quality_summary']['overall_quality_score']}/100")
        print(f"유효 데이터 비율: {report['quality_summary']['valid_rate']:.1f}%")
        print(f"데이터 건강도: {report['data_health']['grade']}")
        print(f"감지된 이상: {report['anomaly_analysis']['total_anomalies']}개")
        
        # 품질 분포
        quality_dist = report['quality_summary']['quality_distribution']
        print(f"\n품질 분포:")
        print(f"  우수: {quality_dist['excellent']}개")
        print(f"  양호: {quality_dist['good']}개")
        print(f"  보통: {quality_dist['fair']}개")
        print(f"  불량: {quality_dist['poor']}개")
        
        # 주요 이슈
        if report['quality_summary']['common_issues']:
            print(f"\n주요 품질 이슈:")
            for issue, count in list(report['quality_summary']['common_issues'].items())[:3]:
                print(f"  {issue}: {count}건")
        
        # 개선 권장사항
        if report['quality_summary']['recommendations']:
            print(f"\n=== 개선 권장사항 ===")
            for i, rec in enumerate(report['quality_summary']['recommendations'], 1):
                print(f"{i}. {rec}")
        
        # 대시보드 데이터 생성
        if args.dashboard:
            print(f"\n대시보드 데이터 생성 중...")
            dashboard_data = reporter.generate_quality_dashboard_data()
            print(f"✅ 대시보드 데이터 생성 완료")
        
        # 주간 요약 생성
        if args.weekly:
            # 해당 주의 시작일 계산
            report_dt = datetime.strptime(report_date, '%Y%m%d')
            week_start = report_dt - timedelta(days=report_dt.weekday())
            week_start_str = week_start.strftime('%Y%m%d')
            
            print(f"\n주간 요약 생성 중... (주 시작: {week_start_str})")
            weekly_summary = reporter.generate_weekly_summary(week_start_str)
            print(f"✅ 주간 요약 생성 완료")
        
        print(f"\n✅ 품질 리포트가 저장되었습니다:")
        print(f"   data/raw/metadata/quality_reports/daily_quality_report_{report_date}.json")
        print(f"   data/raw/metadata/quality_reports/latest_quality_report.json")
        
    except Exception as e:
        print(f"❌ 리포트 생성 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
