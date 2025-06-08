"""
백업 관리 시스템
데이터 파일의 자동 백업, 압축, 아카이브 관리
"""

import os
import shutil
import gzip
import tarfile
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

class BackupManager:
    """데이터 백업 관리자"""
    
    def __init__(self, data_dir: str = 'data', backup_dir: str = 'data/backup'):
        self.data_dir = Path(data_dir)
        self.backup_dir = Path(backup_dir)
        self.logger = logging.getLogger(__name__)
        
        # 백업 설정
        self.backup_config = {
            'retention_days': {
                'daily': 30,      # 일일 백업 30일 보관
                'weekly': 90,     # 주간 백업 90일 보관
                'monthly': 365    # 월간 백업 1년 보관
            },
            'compression': True,
            'checksum_verification': True,
            'max_backup_size_gb': 50  # 최대 백업 크기
        }
        
        # 백업 디렉토리 생성
        self._create_backup_directories()
    
    def _create_backup_directories(self):
        """백업 디렉토리 구조 생성"""
        backup_dirs = [
            'daily', 'weekly', 'monthly', 'archive',
            'metadata', 'checksums', 'logs'
        ]
        
        for backup_type in backup_dirs:
            (self.backup_dir / backup_type).mkdir(parents=True, exist_ok=True)
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """파일 체크섬 계산"""
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            self.logger.error(f"체크섬 계산 실패 {file_path}: {e}")
            return ""
    
    def _compress_file(self, source_path: Path, dest_path: Path) -> bool:
        """파일 압축"""
        try:
            with open(source_path, 'rb') as f_in:
                with gzip.open(dest_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return True
        except Exception as e:
            self.logger.error(f"파일 압축 실패 {source_path}: {e}")
            return False
    
    def _create_tar_archive(self, source_paths: List[Path], archive_path: Path) -> bool:
        """TAR 아카이브 생성"""
        try:
            with tarfile.open(archive_path, 'w:gz') as tar:
                for source_path in source_paths:
                    if source_path.exists():
                        # 상대 경로로 추가
                        arcname = source_path.relative_to(self.data_dir)
                        tar.add(source_path, arcname=arcname)
            return True
        except Exception as e:
            self.logger.error(f"아카이브 생성 실패 {archive_path}: {e}")
            return False
    
    def create_daily_backup(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """일일 백업 생성"""
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime('%Y%m%d')
        backup_info = {
            'backup_type': 'daily',
            'backup_date': date_str,
            'start_time': datetime.now().isoformat(),
            'files_backed_up': [],
            'total_size_bytes': 0,
            'compression_ratio': 0,
            'checksums': {},
            'success': False
        }
        
        self.logger.info(f"일일 백업 시작: {date_str}")
        
        try:
            # 당일 생성된 데이터 파일들 찾기
            daily_files = []
            for pattern in ['*.json', '*.csv', '*.parquet']:
                daily_files.extend(
                    self.data_dir.rglob(pattern)
                )
            
            # 날짜 필터링
            filtered_files = []
            for file_path in daily_files:
                try:
                    file_date = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_date.date() == date.date():
                        filtered_files.append(file_path)
                except Exception:
                    continue
            
            if not filtered_files:
                self.logger.warning(f"백업할 파일이 없습니다: {date_str}")
                backup_info['success'] = True
                return backup_info
            
            # 백업 디렉토리 생성
            daily_backup_dir = self.backup_dir / 'daily' / date_str
            daily_backup_dir.mkdir(parents=True, exist_ok=True)
            
            total_original_size = 0
            total_backup_size = 0
            
            for source_file in filtered_files:
                try:
                    # 원본 파일 크기
                    original_size = source_file.stat().st_size
                    total_original_size += original_size
                    
                    # 백업 파일 경로
                    relative_path = source_file.relative_to(self.data_dir)
                    backup_file = daily_backup_dir / relative_path
                    backup_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    if self.backup_config['compression']:
                        # 압축 백업
                        compressed_file = backup_file.with_suffix(backup_file.suffix + '.gz')
                        if self._compress_file(source_file, compressed_file):
                            backup_size = compressed_file.stat().st_size
                            backup_info['files_backed_up'].append({
                                'source': str(source_file),
                                'backup': str(compressed_file),
                                'original_size': original_size,
                                'backup_size': backup_size,
                                'compressed': True
                            })
                        else:
                            continue
                    else:
                        # 일반 복사
                        shutil.copy2(source_file, backup_file)
                        backup_size = backup_file.stat().st_size
                        backup_info['files_backed_up'].append({
                            'source': str(source_file),
                            'backup': str(backup_file),
                            'original_size': original_size,
                            'backup_size': backup_size,
                            'compressed': False
                        })
                    
                    total_backup_size += backup_size
                    
                    # 체크섬 계산
                    if self.backup_config['checksum_verification']:
                        backup_path = compressed_file if self.backup_config['compression'] else backup_file
                        checksum = self._calculate_checksum(source_file)
                        if checksum:
                            backup_info['checksums'][str(source_file)] = checksum
                
                except Exception as e:
                    self.logger.error(f"파일 백업 실패 {source_file}: {e}")
                    continue
            
            # 백업 통계 계산
            backup_info['total_size_bytes'] = total_backup_size
            if total_original_size > 0:
                backup_info['compression_ratio'] = (1 - total_backup_size / total_original_size) * 100
            
            # 메타데이터 저장
            metadata_file = self.backup_dir / 'metadata' / f'daily_backup_{date_str}.json'
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2, default=str)
            
            backup_info['end_time'] = datetime.now().isoformat()
            backup_info['success'] = True
            
            self.logger.info(f"일일 백업 완료: {len(backup_info['files_backed_up'])}개 파일, "
                           f"{total_backup_size/1024/1024:.1f}MB")
            
        except Exception as e:
            self.logger.error(f"일일 백업 실패: {e}")
            backup_info['error'] = str(e)
        
        return backup_info
    
    def create_weekly_backup(self, year: int, week: int) -> Dict[str, Any]:
        """주간 백업 생성"""
        backup_info = {
            'backup_type': 'weekly',
            'year': year,
            'week': week,
            'start_time': datetime.now().isoformat(),
            'archived_files': [],
            'total_size_bytes': 0,
            'success': False
        }
        
        self.logger.info(f"주간 백업 시작: {year}년 {week}주차")
        
        try:
            # 해당 주의 일일 백업들 찾기
            daily_backup_dir = self.backup_dir / 'daily'
            weekly_files = []
            
            # 주차에 해당하는 날짜들 계산
            from datetime import datetime, timedelta
            jan_4 = datetime(year, 1, 4)
            week_start = jan_4 + timedelta(days=(week - 1) * 7 - jan_4.weekday())
            
            for i in range(7):
                day = week_start + timedelta(days=i)
                day_str = day.strftime('%Y%m%d')
                day_backup_dir = daily_backup_dir / day_str
                
                if day_backup_dir.exists():
                    weekly_files.extend(day_backup_dir.rglob('*'))
            
            if not weekly_files:
                self.logger.warning(f"주간 백업할 파일이 없습니다: {year}년 {week}주차")
                backup_info['success'] = True
                return backup_info
            
            # 주간 아카이브 생성
            archive_name = f'weekly_backup_{year}_W{week:02d}.tar.gz'
            archive_path = self.backup_dir / 'weekly' / archive_name
            
            if self._create_tar_archive(weekly_files, archive_path):
                backup_info['archived_files'] = [str(f) for f in weekly_files]
                backup_info['total_size_bytes'] = archive_path.stat().st_size
                backup_info['archive_path'] = str(archive_path)
                
                # 메타데이터 저장
                metadata_file = self.backup_dir / 'metadata' / f'weekly_backup_{year}_W{week:02d}.json'
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_info, f, ensure_ascii=False, indent=2, default=str)
                
                backup_info['success'] = True
                self.logger.info(f"주간 백업 완료: {len(weekly_files)}개 파일, "
                               f"{backup_info['total_size_bytes']/1024/1024:.1f}MB")
            
        except Exception as e:
            self.logger.error(f"주간 백업 실패: {e}")
            backup_info['error'] = str(e)
        
        backup_info['end_time'] = datetime.now().isoformat()
        return backup_info
    
    def create_monthly_backup(self, year: int, month: int) -> Dict[str, Any]:
        """월간 백업 생성"""
        backup_info = {
            'backup_type': 'monthly',
            'year': year,
            'month': month,
            'start_time': datetime.now().isoformat(),
            'archived_files': [],
            'total_size_bytes': 0,
            'success': False
        }
        
        self.logger.info(f"월간 백업 시작: {year}년 {month}월")
        
        try:
            # 해당 월의 모든 데이터 파일들 찾기
            monthly_files = []
            
            # raw 데이터에서 해당 월 파일들 찾기
            for data_type in ['movies', 'metadata']:
                data_type_dir = self.data_dir / 'raw' / data_type
                if data_type_dir.exists():
                    for file_path in data_type_dir.rglob('*'):
                        if file_path.is_file():
                            try:
                                file_date = datetime.fromtimestamp(file_path.stat().st_mtime)
                                if file_date.year == year and file_date.month == month:
                                    monthly_files.append(file_path)
                            except Exception:
                                continue
            
            # processed 데이터도 포함
            processed_dir = self.data_dir / 'processed'
            if processed_dir.exists():
                for file_path in processed_dir.rglob('*'):
                    if file_path.is_file():
                        try:
                            file_date = datetime.fromtimestamp(file_path.stat().st_mtime)
                            if file_date.year == year and file_date.month == month:
                                monthly_files.append(file_path)
                        except Exception:
                            continue
            
            if not monthly_files:
                self.logger.warning(f"월간 백업할 파일이 없습니다: {year}년 {month}월")
                backup_info['success'] = True
                return backup_info
            
            # 월간 아카이브 생성
            archive_name = f'monthly_backup_{year}_{month:02d}.tar.gz'
            archive_path = self.backup_dir / 'monthly' / archive_name
            
            if self._create_tar_archive(monthly_files, archive_path):
                backup_info['archived_files'] = [str(f) for f in monthly_files]
                backup_info['total_size_bytes'] = archive_path.stat().st_size
                backup_info['archive_path'] = str(archive_path)
                
                # 메타데이터 저장
                metadata_file = self.backup_dir / 'metadata' / f'monthly_backup_{year}_{month:02d}.json'
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_info, f, ensure_ascii=False, indent=2, default=str)
                
                backup_info['success'] = True
                self.logger.info(f"월간 백업 완료: {len(monthly_files)}개 파일, "
                               f"{backup_info['total_size_bytes']/1024/1024:.1f}MB")
            
        except Exception as e:
            self.logger.error(f"월간 백업 실패: {e}")
            backup_info['error'] = str(e)
        
        backup_info['end_time'] = datetime.now().isoformat()
        return backup_info
    
    def cleanup_old_backups(self) -> Dict[str, Any]:
        """오래된 백업 정리"""
        cleanup_info = {
            'start_time': datetime.now().isoformat(),
            'cleaned_backups': {
                'daily': [],
                'weekly': [],
                'monthly': []
            },
            'total_space_freed_bytes': 0,
            'success': False
        }
        
        self.logger.info("오래된 백업 정리 시작")
        
        try:
            current_date = datetime.now()
            total_freed = 0
            
            # 백업 유형별 정리
            for backup_type, retention_days in self.backup_config['retention_days'].items():
                cutoff_date = current_date - timedelta(days=retention_days)
                backup_type_dir = self.backup_dir / backup_type
                
                if not backup_type_dir.exists():
                    continue
                
                # 오래된 백업 파일들 찾기
                for backup_file in backup_type_dir.rglob('*'):
                    if backup_file.is_file():
                        try:
                            file_date = datetime.fromtimestamp(backup_file.stat().st_mtime)
                            if file_date < cutoff_date:
                                file_size = backup_file.stat().st_size
                                backup_file.unlink()
                                
                                cleanup_info['cleaned_backups'][backup_type].append({
                                    'file': str(backup_file),
                                    'size_bytes': file_size,
                                    'age_days': (current_date - file_date).days
                                })
                                total_freed += file_size
                                
                        except Exception as e:
                            self.logger.error(f"백업 파일 정리 실패 {backup_file}: {e}")
                            continue
            
            cleanup_info['total_space_freed_bytes'] = total_freed
            cleanup_info['success'] = True
            
            self.logger.info(f"백업 정리 완료: {total_freed/1024/1024:.1f}MB 정리")
            
        except Exception as e:
            self.logger.error(f"백업 정리 실패: {e}")
            cleanup_info['error'] = str(e)
        
        cleanup_info['end_time'] = datetime.now().isoformat()
        return cleanup_info
    
    def restore_backup(self, backup_path: str, restore_path: str = None) -> Dict[str, Any]:
        """백업 복원"""
        backup_file = Path(backup_path)
        restore_info = {
            'backup_path': backup_path,
            'restore_path': restore_path,
            'start_time': datetime.now().isoformat(),
            'restored_files': [],
            'success': False
        }
        
        if restore_path is None:
            restore_path = str(self.data_dir / 'restored')
        
        restore_dir = Path(restore_path)
        restore_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"백업 복원 시작: {backup_path} → {restore_path}")
        
        try:
            if backup_file.suffix == '.gz' and backup_file.stem.endswith('.tar'):
                # TAR 아카이브 복원
                with tarfile.open(backup_file, 'r:gz') as tar:
                    tar.extractall(path=restore_dir)
                    restore_info['restored_files'] = tar.getnames()
                    
            elif backup_file.suffix == '.gz':
                # 압축 파일 복원
                restored_file = restore_dir / backup_file.stem
                with gzip.open(backup_file, 'rb') as f_in:
                    with open(restored_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                restore_info['restored_files'] = [str(restored_file)]
                
            else:
                # 일반 파일 복사
                restored_file = restore_dir / backup_file.name
                shutil.copy2(backup_file, restored_file)
                restore_info['restored_files'] = [str(restored_file)]
            
            restore_info['success'] = True
            self.logger.info(f"백업 복원 완료: {len(restore_info['restored_files'])}개 파일")
            
        except Exception as e:
            self.logger.error(f"백업 복원 실패: {e}")
            restore_info['error'] = str(e)
        
        restore_info['end_time'] = datetime.now().isoformat()
        return restore_info
    
    def verify_backup_integrity(self, backup_date: str = None) -> Dict[str, Any]:
        """백업 무결성 검증"""
        verify_info = {
            'backup_date': backup_date,
            'start_time': datetime.now().isoformat(),
            'verified_files': [],
            'integrity_issues': [],
            'success': False
        }
        
        if backup_date is None:
            backup_date = datetime.now().strftime('%Y%m%d')
        
        self.logger.info(f"백업 무결성 검증 시작: {backup_date}")
        
        try:
            # 메타데이터 파일 확인
            metadata_file = self.backup_dir / 'metadata' / f'daily_backup_{backup_date}.json'
            
            if not metadata_file.exists():
                verify_info['integrity_issues'].append(f"메타데이터 파일 없음: {metadata_file}")
                return verify_info
            
            with open(metadata_file, 'r', encoding='utf-8') as f:
                backup_metadata = json.load(f)
            
            # 백업 파일들 존재 확인
            for file_info in backup_metadata.get('files_backed_up', []):
                backup_file_path = Path(file_info['backup'])
                
                if not backup_file_path.exists():
                    verify_info['integrity_issues'].append(f"백업 파일 없음: {backup_file_path}")
                    continue
                
                # 파일 크기 확인
                actual_size = backup_file_path.stat().st_size
                expected_size = file_info['backup_size']
                
                if actual_size != expected_size:
                    verify_info['integrity_issues'].append(
                        f"파일 크기 불일치 {backup_file_path}: "
                        f"예상 {expected_size}, 실제 {actual_size}"
                    )
                    continue
                
                verify_info['verified_files'].append(str(backup_file_path))
            
            # 체크섬 검증
            if self.backup_config['checksum_verification']:
                checksums = backup_metadata.get('checksums', {})
                for source_file, expected_checksum in checksums.items():
                    source_path = Path(source_file)
                    if source_path.exists():
                        actual_checksum = self._calculate_checksum(source_path)
                        if actual_checksum != expected_checksum:
                            verify_info['integrity_issues'].append(
                                f"체크섬 불일치 {source_file}: "
                                f"예상 {expected_checksum[:8]}..., 실제 {actual_checksum[:8]}..."
                            )
            
            verify_info['success'] = len(verify_info['integrity_issues']) == 0
            
            if verify_info['success']:
                self.logger.info(f"백업 무결성 검증 성공: {len(verify_info['verified_files'])}개 파일")
            else:
                self.logger.warning(f"백업 무결성 이슈 발견: {len(verify_info['integrity_issues'])}개")
            
        except Exception as e:
            self.logger.error(f"백업 무결성 검증 실패: {e}")
            verify_info['error'] = str(e)
        
        verify_info['end_time'] = datetime.now().isoformat()
        return verify_info
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """백업 통계 조회"""
        stats = {
            'total_backups': {
                'daily': 0,
                'weekly': 0,
                'monthly': 0
            },
            'total_size_bytes': {
                'daily': 0,
                'weekly': 0,
                'monthly': 0
            },
            'oldest_backup': None,
            'newest_backup': None,
            'backup_health': 'unknown'
        }
        
        try:
            oldest_date = None
            newest_date = None
            
            for backup_type in ['daily', 'weekly', 'monthly']:
                backup_type_dir = self.backup_dir / backup_type
                if backup_type_dir.exists():
                    backup_files = list(backup_type_dir.rglob('*'))
                    stats['total_backups'][backup_type] = len([f for f in backup_files if f.is_file()])
                    
                    total_size = sum(f.stat().st_size for f in backup_files if f.is_file())
                    stats['total_size_bytes'][backup_type] = total_size
                    
                    # 날짜 추적
                    for backup_file in backup_files:
                        if backup_file.is_file():
                            file_date = datetime.fromtimestamp(backup_file.stat().st_mtime)
                            if oldest_date is None or file_date < oldest_date:
                                oldest_date = file_date
                            if newest_date is None or file_date > newest_date:
                                newest_date = file_date
            
            stats['oldest_backup'] = oldest_date.isoformat() if oldest_date else None
            stats['newest_backup'] = newest_date.isoformat() if newest_date else None
            
            # 백업 건강도 평가
            total_backups = sum(stats['total_backups'].values())
            if total_backups == 0:
                stats['backup_health'] = 'no_backups'
            elif newest_date and (datetime.now() - newest_date).days > 7:
                stats['backup_health'] = 'stale'
            elif total_backups < 7:  # 일주일치 미만
                stats['backup_health'] = 'insufficient'
            else:
                stats['backup_health'] = 'healthy'
            
            # 총 크기 계산
            stats['total_size_all_bytes'] = sum(stats['total_size_bytes'].values())
            stats['total_size_all_gb'] = stats['total_size_all_bytes'] / (1024 ** 3)
            
        except Exception as e:
            self.logger.error(f"백업 통계 조회 실패: {e}")
            stats['error'] = str(e)
        
        return stats

def main():
    """백업 관리 도구 메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='데이터 백업 관리 도구')
    subparsers = parser.add_subparsers(dest='command', help='사용 가능한 명령어')
    
    # 일일 백업
    daily_parser = subparsers.add_parser('daily', help='일일 백업 생성')
    daily_parser.add_argument('--date', help='백업 날짜 (YYYYMMDD)')
    
    # 주간 백업
    weekly_parser = subparsers.add_parser('weekly', help='주간 백업 생성')
    weekly_parser.add_argument('--year', type=int, help='백업 년도')
    weekly_parser.add_argument('--week', type=int, help='백업 주차')
    
    # 월간 백업
    monthly_parser = subparsers.add_parser('monthly', help='월간 백업 생성')
    monthly_parser.add_argument('--year', type=int, help='백업 년도')
    monthly_parser.add_argument('--month', type=int, help='백업 월')
    
    # 정리
    subparsers.add_parser('cleanup', help='오래된 백업 정리')
    
    # 복원
    restore_parser = subparsers.add_parser('restore', help='백업 복원')
    restore_parser.add_argument('backup_path', help='복원할 백업 파일 경로')
    restore_parser.add_argument('--restore_path', help='복원 위치')
    
    # 검증
    verify_parser = subparsers.add_parser('verify', help='백업 무결성 검증')
    verify_parser.add_argument('--date', help='검증할 백업 날짜 (YYYYMMDD)')
    
    # 통계
    subparsers.add_parser('stats', help='백업 통계 조회')
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    backup_manager = BackupManager()
    
    try:
        if args.command == 'daily':
            date = datetime.strptime(args.date, '%Y%m%d') if args.date else None
            result = backup_manager.create_daily_backup(date)
            print(f"일일 백업 결과: {result['success']}")
            
        elif args.command == 'weekly':
            year = args.year or datetime.now().year
            week = args.week or datetime.now().isocalendar()[1]
            result = backup_manager.create_weekly_backup(year, week)
            print(f"주간 백업 결과: {result['success']}")
            
        elif args.command == 'monthly':
            year = args.year or datetime.now().year
            month = args.month or datetime.now().month
            result = backup_manager.create_monthly_backup(year, month)
            print(f"월간 백업 결과: {result['success']}")
            
        elif args.command == 'cleanup':
            result = backup_manager.cleanup_old_backups()
            print(f"백업 정리 결과: {result['success']}")
            if result['success']:
                freed_mb = result['total_space_freed_bytes'] / 1024 / 1024
                print(f"정리된 용량: {freed_mb:.1f}MB")
                
        elif args.command == 'restore':
            result = backup_manager.restore_backup(args.backup_path, args.restore_path)
            print(f"백업 복원 결과: {result['success']}")
            
        elif args.command == 'verify':
            result = backup_manager.verify_backup_integrity(args.date)
            print(f"백업 검증 결과: {result['success']}")
            if not result['success']:
                for issue in result['integrity_issues']:
                    print(f"  이슈: {issue}")
                    
        elif args.command == 'stats':
            stats = backup_manager.get_backup_statistics()
            print("\n=== 백업 통계 ===")
            for backup_type, count in stats['total_backups'].items():
                size_mb = stats['total_size_bytes'][backup_type] / 1024 / 1024
                print(f"{backup_type:8}: {count:3d}개, {size_mb:8.1f}MB")
            
            print(f"\n총 용량: {stats['total_size_all_gb']:.2f}GB")
            print(f"백업 상태: {stats['backup_health']}")
            
    except Exception as e:
        print(f"명령 실행 실패: {e}")

if __name__ == "__main__":
    main()
