#!/usr/bin/env python3
"""
종합 로그 관리 스크립트
로그 분석, 정리, 모니터링을 통합 관리
"""

import sys
import argparse
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import subprocess

# 프로젝트 경로 설정
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / 'src'))

from logging_system.analyzers.log_analyzer import LogAnalyzer, generate_daily_log_report

class LogManager:
    """종합 로그 관리자"""
    
    def __init__(self, log_dir='logs'):
        self.log_dir = Path(log_dir)
        self.analyzer = LogAnalyzer(log_dir)
    
    def clean_old_logs(self, days=30):
        """오래된 로그 파일 정리"""
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_files = []
        total_size_saved = 0
        
        print(f"🧹 {days}일 이전 로그 파일 정리 중...")
        
        for log_file in self.log_dir.rglob('*.log'):
            try:
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    file_size = log_file.stat().st_size
                    log_file.unlink()
                    cleaned_files.append(str(log_file))
                    total_size_saved += file_size
            except Exception as e:
                print(f"파일 정리 실패 {log_file}: {e}")
        
        print(f"✅ 정리 완료: {len(cleaned_files)}개 파일, {total_size_saved/1024/1024:.1f}MB 절약")
        return cleaned_files
    
    def compress_logs(self, days=7):
        """오래된 로그 파일 압축"""
        import gzip
        import shutil
        
        cutoff_date = datetime.now() - timedelta(days=days)
        compressed_files = []
        
        print(f"📦 {days}일 이전 로그 파일 압축 중...")
        
        for log_file in self.log_dir.rglob('*.log'):
            try:
                if (log_file.stat().st_mtime < cutoff_date.timestamp() and 
                    not log_file.name.endswith('.gz')):
                    
                    compressed_path = log_file.with_suffix(log_file.suffix + '.gz')
                    
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(compressed_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    log_file.unlink()
                    compressed_files.append(str(compressed_path))
                    
            except Exception as e:
                print(f"압축 실패 {log_file}: {e}")
        
        print(f"✅ 압축 완료: {len(compressed_files)}개 파일")
        return compressed_files
    
    def archive_logs(self, year=None, month=None):
        """로그 파일 아카이브"""
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        
        archive_dir = self.log_dir / 'archive' / str(year) / f"{month:02d}"
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        archived_files = []
        
        print(f"📚 {year}년 {month}월 로그 아카이브 중...")
        
        # 해당 월의 로그 파일들 찾기
        for log_file in self.log_dir.rglob('*.log*'):
            try:
                file_date = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_date.year == year and file_date.month == month:
                    if 'archive' not in str(log_file):  # 이미 아카이브된 파일 제외
                        dest_file = archive_dir / log_file.name
                        log_file.rename(dest_file)
                        archived_files.append(str(dest_file))
            except Exception as e:
                print(f"아카이브 실패 {log_file}: {e}")
        
        print(f"✅ 아카이브 완료: {len(archived_files)}개 파일 → {archive_dir}")
        return archived_files
    
    def get_disk_usage(self):
        """로그 디스크 사용량 분석"""
        usage_stats = {}
        total_size = 0
        
        for subdir in ['app', 'error', 'system', 'audit', 'performance', 'reports', 'archive']:
            subdir_path = self.log_dir / subdir
            if subdir_path.exists():
                size = sum(f.stat().st_size for f in subdir_path.rglob('*') if f.is_file())
                file_count = len(list(subdir_path.rglob('*')))
                usage_stats[subdir] = {
                    'size_bytes': size,
                    'size_mb': size / 1024 / 1024,
                    'file_count': file_count
                }
                total_size += size
        
        usage_stats['total'] = {
            'size_bytes': total_size,
            'size_mb': total_size / 1024 / 1024,
            'size_gb': total_size / 1024 / 1024 / 1024
        }
        
        return usage_stats
    
    def monitor_log_growth(self, hours=24):
        """로그 증가율 모니터링"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        growth_stats = {}
        
        for subdir in ['app', 'error', 'system', 'performance']:
            subdir_path = self.log_dir / subdir
            if subdir_path.exists():
                recent_size = 0
                recent_files = 0
                
                for log_file in subdir_path.rglob('*.log'):
                    try:
                        if datetime.fromtimestamp(log_file.stat().st_mtime) > cutoff_time:
                            recent_size += log_file.stat().st_size
                            recent_files += 1
                    except Exception:
                        continue
                
                growth_stats[subdir] = {
                    'recent_size_mb': recent_size / 1024 / 1024,
                    'recent_files': recent_files,
                    'growth_rate_mb_per_hour': (recent_size / 1024 / 1024) / hours
                }
        
        return growth_stats
    
    def generate_maintenance_report(self):
        """로그 유지보수 리포트 생성"""
        usage_stats = self.get_disk_usage()
        growth_stats = self.monitor_log_growth(24)
        
        report = {
            'report_date': datetime.now().isoformat(),
            'disk_usage': usage_stats,
            'growth_analysis': growth_stats,
            'maintenance_recommendations': []
        }
        
        # 유지보수 권장사항 생성
        total_size_gb = usage_stats['total']['size_gb']
        if total_size_gb > 5:
            report['maintenance_recommendations'].append(
                f"로그 총 크기가 {total_size_gb:.1f}GB입니다. 아카이브를 고려하세요."
            )
        
        # 빠르게 증가하는 로그 감지
        for subdir, stats in growth_stats.items():
            if stats['growth_rate_mb_per_hour'] > 10:
                report['maintenance_recommendations'].append(
                    f"{subdir} 로그가 시간당 {stats['growth_rate_mb_per_hour']:.1f}MB로 빠르게 증가하고 있습니다."
                )
        
        if not report['maintenance_recommendations']:
            report['maintenance_recommendations'].append("로그 상태가 양호합니다.")
        
        # 리포트 저장
        report_file = self.log_dir / 'reports' / f"maintenance_report_{datetime.now().strftime('%Y%m%d')}.json"
        report_file.parent.mkdir(exist_ok=True, parents=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        return report
    
    def export_logs(self, start_date, end_date, output_file):
        """특정 기간 로그 내보내기"""
        import tarfile
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        export_files = []
        
        for log_file in self.log_dir.rglob('*.log*'):
            try:
                file_date = datetime.fromtimestamp(log_file.stat().st_mtime)
                if start_dt <= file_date <= end_dt:
                    export_files.append(log_file)
            except Exception:
                continue
        
        with tarfile.open(output_file, 'w:gz') as tar:
            for log_file in export_files:
                tar.add(log_file, arcname=log_file.relative_to(self.log_dir))
        
        print(f"✅ {len(export_files)}개 파일을 {output_file}로 내보냈습니다.")
        return export_files

def analyze_logs(args):
    """로그 분석 실행"""
    analyzer = LogAnalyzer()
    
    if args.type == 'errors':
        result = analyzer.analyze_error_logs(args.hours)
        print(f"\n=== 에러 로그 분석 (최근 {args.hours}시간) ===")
        print(f"총 에러 수: {result['total_errors']}")
        print(f"에러 유형: {result['error_types']}")
        print(f"에러 트렌드: {result['error_trend']}")
        
    elif args.type == 'performance':
        result = analyzer.analyze_performance_logs(args.hours)
        print(f"\n=== 성능 로그 분석 (최근 {args.hours}시간) ===")
        print(f"총 작업 수: {result['total_operations']}")
        print(f"느린 작업 수: {len(result['slow_operations'])}")
        
        if result['component_stats']:
            print("\n컴포넌트별 평균 실행 시간:")
            for comp, stats in result['component_stats'].items():
                print(f"  {comp}: {stats['avg_time']:.3f}s (총 {stats['count']}회)")
        
    elif args.type == 'health':
        result = analyzer.generate_health_report()
        print(f"\n=== 시스템 건강 상태 ===")
        print(f"건강도: {result['grade']} ({result['health_score']}/100)")
        print(f"감지된 이슈: {result['issues']}")
        print("\n권장사항:")
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"  {i}. {rec}")
            
    elif args.type == 'api':
        result = analyzer.analyze_api_usage(args.hours)
        print(f"\n=== API 사용 분석 (최근 {args.hours}시간) ===")
        print(f"총 API 호출: {result['total_api_calls']}")
        print(f"성공률: {result.get('success_rate', 0):.1f}%")
        if 'avg_response_time' in result:
            print(f"평균 응답 시간: {result['avg_response_time']:.3f}s")
        
    elif args.type == 'daily':
        result = generate_daily_log_report()
        print("일일 리포트가 생성되었습니다.")
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, default=str, ensure_ascii=False)
        print(f"\n결과가 {args.output}에 저장되었습니다.")

def manage_logs(args):
    """로그 관리 실행"""
    manager = LogManager()
    
    if args.action == 'clean':
        manager.clean_old_logs(args.days)
    elif args.action == 'compress':
        manager.compress_logs(args.days)
    elif args.action == 'archive':
        manager.archive_logs()
    elif args.action == 'usage':
        usage = manager.get_disk_usage()
        print("\n=== 로그 디스크 사용량 ===")
        for subdir, stats in usage.items():
            if subdir != 'total':
                print(f"{subdir:15}: {stats['file_count']:4d}개 파일, {stats['size_mb']:8.1f}MB")
        print("-" * 40)
        print(f"{'총계':15}: {usage['total']['size_mb']:8.1f}MB ({usage['total']['size_gb']:.2f}GB)")
    elif args.action == 'growth':
        growth = manager.monitor_log_growth(24)
        print("\n=== 로그 증가율 (24시간) ===")
        for subdir, stats in growth.items():
            print(f"{subdir:15}: {stats['growth_rate_mb_per_hour']:6.2f}MB/h, {stats['recent_files']:3d}개 파일")
    elif args.action == 'maintenance':
        report = manager.generate_maintenance_report()
        print("\n=== 유지보수 리포트 ===")
        print(f"총 사용량: {report['disk_usage']['total']['size_gb']:.2f}GB")
        print("\n권장사항:")
        for i, rec in enumerate(report['maintenance_recommendations'], 1):
            print(f"  {i}. {rec}")

def show_stats(args):
    """로그 통계 표시"""
    log_dir = Path('logs')
    
    print("\n=== 로그 디렉토리 통계 ===")
    
    for subdir in ['app', 'error', 'system', 'audit', 'performance', 'reports', 'archive']:
        subdir_path = log_dir / subdir
        if subdir_path.exists():
            files = list(subdir_path.rglob('*'))
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            
            print(f"{subdir:12}: {len(files):3d}개 파일, {total_size/1024/1024:8.1f}MB")
        else:
            print(f"{subdir:12}: 디렉토리 없음")

def tail_logs(args):
    """로그 실시간 모니터링"""
    log_file = Path('logs') / args.type / f"{args.file}.log"
    
    if not log_file.exists():
        print(f"로그 파일을 찾을 수 없습니다: {log_file}")
        return
    
    print(f"🔍 {log_file} 실시간 모니터링 (Ctrl+C로 종료)")
    
    try:
        # tail -f 명령어 실행
        process = subprocess.Popen(['tail', '-f', str(log_file)], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 universal_newlines=True)
        
        for line in process.stdout:
            print(line.rstrip())
            
    except KeyboardInterrupt:
        print("\n모니터링을 중단합니다.")
        process.terminate()
    except Exception as e:
        print(f"모니터링 오류: {e}")

def main():
    parser = argparse.ArgumentParser(description='Movie MLOps 로그 관리 도구')
    subparsers = parser.add_subparsers(dest='command', help='사용 가능한 명령어')
    
    # 로그 분석
    analyze_parser = subparsers.add_parser('analyze', help='로그 분석')
    analyze_parser.add_argument('type', choices=['errors', 'performance', 'health', 'api', 'daily'],
                               help='분석 유형')
    analyze_parser.add_argument('--hours', type=int, default=24,
                               help='분석 기간 (시간, 기본값: 24)')
    analyze_parser.add_argument('--output', help='결과 저장 파일')
    analyze_parser.set_defaults(func=analyze_logs)
    
    # 로그 관리
    manage_parser = subparsers.add_parser('manage', help='로그 관리')
    manage_parser.add_argument('action', choices=['clean', 'compress', 'archive', 'usage', 'growth', 'maintenance'],
                              help='관리 작업')
    manage_parser.add_argument('--days', type=int, default=30,
                              help='작업 대상 일수 (기본값: 30)')
    manage_parser.set_defaults(func=manage_logs)
    
    # 통계 표시
    stats_parser = subparsers.add_parser('stats', help='로그 통계')
    stats_parser.set_defaults(func=show_stats)
    
    # 실시간 모니터링
    tail_parser = subparsers.add_parser('tail', help='로그 실시간 모니터링')
    tail_parser.add_argument('type', choices=['app', 'error', 'system', 'performance'],
                            help='로그 유형')
    tail_parser.add_argument('file', help='로그 파일명 (확장자 제외)')
    tail_parser.set_defaults(func=tail_logs)
    
    # 인수 파싱 및 실행
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    try:
        args.func(args)
    except Exception as e:
        print(f"오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
