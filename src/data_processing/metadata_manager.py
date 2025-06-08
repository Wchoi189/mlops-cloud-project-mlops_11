"""
메타데이터 관리 시스템
데이터 파일의 메타데이터를 체계적으로 관리하고 추적
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import logging

class MetadataManager:
    """데이터 메타데이터 관리자"""
    
    def __init__(self, data_dir: str = 'data', metadata_dir: str = 'data/raw/metadata'):
        self.data_dir = Path(data_dir)
        self.metadata_dir = Path(metadata_dir)
        self.logger = logging.getLogger(__name__)
        
        # 메타데이터 디렉토리 구조 생성
        self._create_metadata_directories()
        
        # 메타데이터 스키마 정의
        self.schemas = self._load_schemas()
    
    def _create_metadata_directories(self):
        """메타데이터 디렉토리 구조 생성"""
        metadata_dirs = [
            'schemas', 'quality_reports', 'collection_stats',
            'lineage', 'versions', 'catalogs'
        ]
        
        for dir_name in metadata_dirs:
            (self.metadata_dir / dir_name).mkdir(parents=True, exist_ok=True)
    
    def _load_schemas(self) -> Dict[str, Any]:
        """메타데이터 스키마 로드"""
        schemas = {
            'file_metadata': {
                'file_path': str,
                'file_name': str,
                'file_size_bytes': int,
                'file_type': str,
                'created_date': str,
                'modified_date': str,
                'checksum_sha256': str,
                'data_type': str,  # 'raw', 'processed', 'backup'
                'collection_info': dict,
                'quality_metrics': dict,
                'lineage': dict,
                'tags': list,
                'version': str
            },
            'collection_metadata': {
                'collection_id': str,
                'collection_type': str,
                'collection_date': str,
                'start_time': str,
                'end_time': str,
                'duration_seconds': float,
                'records_collected': int,
                'api_calls_made': int,
                'success_rate': float,
                'data_sources': list,
                'collection_config': dict,
                'quality_summary': dict
            },
            'quality_metadata': {
                'quality_id': str,
                'file_path': str,
                'validation_date': str,
                'validator_version': str,
                'total_records': int,
                'valid_records': int,
                'invalid_records': int,
                'validation_rate': float,
                'quality_score': float,
                'validation_rules': list,
                'issues_found': list,
                'recommendations': list
            }
        }
        
        # 스키마 파일에 저장
        schema_file = self.metadata_dir / 'schemas' / 'metadata_schemas.json'
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(schemas, f, ensure_ascii=False, indent=2, default=str)
        
        return schemas
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
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
    
    def _validate_metadata(self, metadata: Dict[str, Any], schema_name: str) -> bool:
        """메타데이터 스키마 검증"""
        if schema_name not in self.schemas:
            self.logger.error(f"알 수 없는 스키마: {schema_name}")
            return False
        
        schema = self.schemas[schema_name]
        
        # 필수 필드 검증
        for field_name, field_type in schema.items():
            if field_name not in metadata:
                self.logger.error(f"필수 필드 누락: {field_name}")
                return False
            
            # 타입 검증 (기본적인 검증만)
            if field_type == str and not isinstance(metadata[field_name], str):
                if metadata[field_name] is not None:
                    metadata[field_name] = str(metadata[field_name])
            elif field_type == int and not isinstance(metadata[field_name], int):
                try:
                    metadata[field_name] = int(metadata[field_name])
                except (ValueError, TypeError):
                    self.logger.error(f"필드 타입 오류 {field_name}: int 필요")
                    return False
            elif field_type == float and not isinstance(metadata[field_name], (int, float)):
                try:
                    metadata[field_name] = float(metadata[field_name])
                except (ValueError, TypeError):
                    self.logger.error(f"필드 타입 오류 {field_name}: float 필요")
                    return False
        
        return True
    
    def create_file_metadata(self, file_path: Union[str, Path], 
                           data_type: str = 'raw',
                           collection_info: Dict[str, Any] = None,
                           quality_metrics: Dict[str, Any] = None,
                           tags: List[str] = None) -> Dict[str, Any]:
        """파일 메타데이터 생성"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        stat = file_path.stat()
        
        metadata = {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'file_size_bytes': stat.st_size,
            'file_type': file_path.suffix.lower(),
            'created_date': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified_date': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'checksum_sha256': self._calculate_file_checksum(file_path),
            'data_type': data_type,
            'collection_info': collection_info or {},
            'quality_metrics': quality_metrics or {},
            'lineage': {
                'created_by': 'metadata_manager',
                'creation_timestamp': datetime.now().isoformat(),
                'parent_files': [],
                'processing_steps': []
            },
            'tags': tags or [],
            'version': '1.0'
        }
        
        # 스키마 검증
        if not self._validate_metadata(metadata, 'file_metadata'):
            raise ValueError("메타데이터 스키마 검증 실패")
        
        # 메타데이터 저장
        metadata_file = self._get_metadata_file_path(file_path, 'file_metadata')
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2, default=str)
        
        self.logger.info(f"파일 메타데이터 생성: {metadata_file}")
        return metadata
    
    def create_collection_metadata(self, collection_id: str,
                                 collection_type: str,
                                 collection_date: str,
                                 start_time: str,
                                 end_time: str,
                                 records_collected: int,
                                 api_calls_made: int = 0,
                                 success_rate: float = 100.0,
                                 data_sources: List[str] = None,
                                 collection_config: Dict[str, Any] = None,
                                 quality_summary: Dict[str, Any] = None) -> Dict[str, Any]:
        """데이터 수집 메타데이터 생성"""
        
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)
        duration = (end_dt - start_dt).total_seconds()
        
        metadata = {
            'collection_id': collection_id,
            'collection_type': collection_type,
            'collection_date': collection_date,
            'start_time': start_time,
            'end_time': end_time,
            'duration_seconds': duration,
            'records_collected': records_collected,
            'api_calls_made': api_calls_made,
            'success_rate': success_rate,
            'data_sources': data_sources or ['TMDB_API'],
            'collection_config': collection_config or {},
            'quality_summary': quality_summary or {}
        }
        
        # 스키마 검증
        if not self._validate_metadata(metadata, 'collection_metadata'):
            raise ValueError("수집 메타데이터 스키마 검증 실패")
        
        # 메타데이터 저장
        metadata_file = self.metadata_dir / 'collection_stats' / f'{collection_id}_metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2, default=str)
        
        self.logger.info(f"수집 메타데이터 생성: {metadata_file}")
        return metadata
    
    def create_quality_metadata(self, quality_id: str,
                              file_path: Union[str, Path],
                              validation_date: str,
                              validator_version: str,
                              total_records: int,
                              valid_records: int,
                              quality_score: float,
                              validation_rules: List[str] = None,
                              issues_found: List[str] = None,
                              recommendations: List[str] = None) -> Dict[str, Any]:
        """데이터 품질 메타데이터 생성"""
        
        invalid_records = total_records - valid_records
        validation_rate = (valid_records / total_records * 100) if total_records > 0 else 0
        
        metadata = {
            'quality_id': quality_id,
            'file_path': str(file_path),
            'validation_date': validation_date,
            'validator_version': validator_version,
            'total_records': total_records,
            'valid_records': valid_records,
            'invalid_records': invalid_records,
            'validation_rate': validation_rate,
            'quality_score': quality_score,
            'validation_rules': validation_rules or [],
            'issues_found': issues_found or [],
            'recommendations': recommendations or []
        }
        
        # 스키마 검증
        if not self._validate_metadata(metadata, 'quality_metadata'):
            raise ValueError("품질 메타데이터 스키마 검증 실패")
        
        # 메타데이터 저장
        metadata_file = self.metadata_dir / 'quality_reports' / f'{quality_id}_metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2, default=str)
        
        self.logger.info(f"품질 메타데이터 생성: {metadata_file}")
        return metadata
    
    def _get_metadata_file_path(self, data_file_path: Path, metadata_type: str) -> Path:
        """메타데이터 파일 경로 생성"""
        # 데이터 파일의 상대 경로 계산
        try:
            relative_path = data_file_path.relative_to(self.data_dir)
        except ValueError:
            # 데이터 디렉토리 외부의 파일인 경우
            relative_path = Path(data_file_path.name)
        
        # 메타데이터 파일명 생성
        metadata_filename = f"{relative_path.stem}_{metadata_type}.json"
        
        # 디렉토리 구조 유지
        metadata_subdir = relative_path.parent
        metadata_dir = self.metadata_dir / 'catalogs' / metadata_subdir
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        return metadata_dir / metadata_filename
    
    def get_file_metadata(self, file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """파일 메타데이터 조회"""
        file_path = Path(file_path)
        metadata_file = self._get_metadata_file_path(file_path, 'file_metadata')
        
        if not metadata_file.exists():
            self.logger.warning(f"메타데이터 파일 없음: {metadata_file}")
            return None
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            return metadata
        except Exception as e:
            self.logger.error(f"메타데이터 읽기 실패 {metadata_file}: {e}")
            return None
    
    def update_file_metadata(self, file_path: Union[str, Path], 
                           updates: Dict[str, Any]) -> bool:
        """파일 메타데이터 업데이트"""
        file_path = Path(file_path)
        metadata = self.get_file_metadata(file_path)
        
        if metadata is None:
            self.logger.error(f"메타데이터를 찾을 수 없습니다: {file_path}")
            return False
        
        # 업데이트 적용
        metadata.update(updates)
        
        # 수정 시간 업데이트
        metadata['lineage']['last_modified'] = datetime.now().isoformat()
        
        # 버전 증가
        current_version = metadata.get('version', '1.0')
        try:
            version_parts = current_version.split('.')
            minor_version = int(version_parts[1]) + 1
            metadata['version'] = f"{version_parts[0]}.{minor_version}"
        except (IndexError, ValueError):
            metadata['version'] = '1.1'
        
        # 스키마 재검증
        if not self._validate_metadata(metadata, 'file_metadata'):
            self.logger.error("업데이트된 메타데이터 스키마 검증 실패")
            return False
        
        # 저장
        metadata_file = self._get_metadata_file_path(file_path, 'file_metadata')
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"메타데이터 업데이트 완료: {metadata_file}")
            return True
        except Exception as e:
            self.logger.error(f"메타데이터 저장 실패 {metadata_file}: {e}")
            return False
    
    def add_lineage_info(self, file_path: Union[str, Path], 
                        parent_files: List[str] = None,
                        processing_step: str = None) -> bool:
        """데이터 리니지 정보 추가"""
        updates = {}
        
        if parent_files:
            metadata = self.get_file_metadata(file_path)
            if metadata:
                current_parents = metadata.get('lineage', {}).get('parent_files', [])
                updated_parents = list(set(current_parents + parent_files))
                updates['lineage'] = metadata.get('lineage', {})
                updates['lineage']['parent_files'] = updated_parents
        
        if processing_step:
            metadata = self.get_file_metadata(file_path)
            if metadata:
                processing_steps = metadata.get('lineage', {}).get('processing_steps', [])
                processing_steps.append({
                    'step': processing_step,
                    'timestamp': datetime.now().isoformat()
                })
                if 'lineage' not in updates:
                    updates['lineage'] = metadata.get('lineage', {})
                updates['lineage']['processing_steps'] = processing_steps
        
        if updates:
            return self.update_file_metadata(file_path, updates)
        
        return True
    
    def search_metadata(self, 
                       data_type: str = None,
                       collection_type: str = None,
                       date_range: tuple = None,
                       tags: List[str] = None,
                       min_quality_score: float = None) -> List[Dict[str, Any]]:
        """메타데이터 검색"""
        results = []
        
        # 파일 메타데이터 검색
        catalog_dir = self.metadata_dir / 'catalogs'
        
        for metadata_file in catalog_dir.rglob('*_file_metadata.json'):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # 필터 적용
                if data_type and metadata.get('data_type') != data_type:
                    continue
                
                if collection_type:
                    collection_info = metadata.get('collection_info', {})
                    if collection_info.get('collection_type') != collection_type:
                        continue
                
                if date_range:
                    start_date, end_date = date_range
                    file_date = metadata.get('created_date', '')
                    if not (start_date <= file_date <= end_date):
                        continue
                
                if tags:
                    file_tags = metadata.get('tags', [])
                    if not any(tag in file_tags for tag in tags):
                        continue
                
                if min_quality_score:
                    quality_metrics = metadata.get('quality_metrics', {})
                    quality_score = quality_metrics.get('quality_score', 0)
                    if quality_score < min_quality_score:
                        continue
                
                results.append(metadata)
                
            except Exception as e:
                self.logger.error(f"메타데이터 읽기 실패 {metadata_file}: {e}")
                continue
        
        return results
    
    def generate_data_catalog(self, output_file: str = None) -> Dict[str, Any]:
        """데이터 카탈로그 생성"""
        catalog = {
            'catalog_version': '1.0',
            'generation_date': datetime.now().isoformat(),
            'total_files': 0,
            'data_types': {},
            'collection_types': {},
            'quality_summary': {
                'avg_quality_score': 0,
                'files_with_quality_data': 0,
                'high_quality_files': 0  # 점수 80 이상
            },
            'size_summary': {
                'total_size_bytes': 0,
                'avg_file_size_bytes': 0,
                'largest_file': None,
                'smallest_file': None
            },
            'files': []
        }
        
        all_metadata = self.search_metadata()
        catalog['total_files'] = len(all_metadata)
        
        quality_scores = []
        file_sizes = []
        
        for metadata in all_metadata:
            # 데이터 타입별 집계
            data_type = metadata.get('data_type', 'unknown')
            catalog['data_types'][data_type] = catalog['data_types'].get(data_type, 0) + 1
            
            # 수집 타입별 집계
            collection_info = metadata.get('collection_info', {})
            collection_type = collection_info.get('collection_type', 'unknown')
            catalog['collection_types'][collection_type] = catalog['collection_types'].get(collection_type, 0) + 1
            
            # 품질 정보 수집
            quality_metrics = metadata.get('quality_metrics', {})
            if 'quality_score' in quality_metrics:
                quality_score = quality_metrics['quality_score']
                quality_scores.append(quality_score)
                if quality_score >= 80:
                    catalog['quality_summary']['high_quality_files'] += 1
            
            # 크기 정보 수집
            file_size = metadata.get('file_size_bytes', 0)
            file_sizes.append(file_size)
            
            # 카탈로그에 포함할 파일 정보
            catalog['files'].append({
                'file_path': metadata.get('file_path'),
                'file_name': metadata.get('file_name'),
                'data_type': data_type,
                'collection_type': collection_type,
                'created_date': metadata.get('created_date'),
                'file_size_bytes': file_size,
                'quality_score': quality_metrics.get('quality_score'),
                'tags': metadata.get('tags', [])
            })
        
        # 품질 요약 계산
        if quality_scores:
            catalog['quality_summary']['avg_quality_score'] = sum(quality_scores) / len(quality_scores)
            catalog['quality_summary']['files_with_quality_data'] = len(quality_scores)
        
        # 크기 요약 계산
        if file_sizes:
            catalog['size_summary']['total_size_bytes'] = sum(file_sizes)
            catalog['size_summary']['avg_file_size_bytes'] = sum(file_sizes) / len(file_sizes)
            
            # 최대/최소 파일 찾기
            max_size = max(file_sizes)
            min_size = min(file_sizes)
            
            for file_info in catalog['files']:
                if file_info['file_size_bytes'] == max_size:
                    catalog['size_summary']['largest_file'] = file_info['file_path']
                if file_info['file_size_bytes'] == min_size:
                    catalog['size_summary']['smallest_file'] = file_info['file_path']
        
        # 카탈로그 저장
        if output_file is None:
            output_file = str(self.metadata_dir / 'data_catalog.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2, default=str)
        
        self.logger.info(f"데이터 카탈로그 생성 완료: {output_file}")
        return catalog
    
    def cleanup_orphaned_metadata(self) -> Dict[str, Any]:
        """고아 메타데이터 정리"""
        cleanup_info = {
            'start_time': datetime.now().isoformat(),
            'orphaned_files': [],
            'cleaned_files': [],
            'errors': []
        }
        
        catalog_dir = self.metadata_dir / 'catalogs'
        
        for metadata_file in catalog_dir.rglob('*_file_metadata.json'):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                data_file_path = Path(metadata.get('file_path', ''))
                
                # 원본 데이터 파일이 존재하는지 확인
                if not data_file_path.exists():
                    cleanup_info['orphaned_files'].append(str(metadata_file))
                    
                    # 고아 메타데이터 파일 삭제
                    metadata_file.unlink()
                    cleanup_info['cleaned_files'].append(str(metadata_file))
                    
            except Exception as e:
                cleanup_info['errors'].append(f"처리 실패 {metadata_file}: {e}")
                continue
        
        cleanup_info['end_time'] = datetime.now().isoformat()
        
        self.logger.info(f"고아 메타데이터 정리 완료: {len(cleanup_info['cleaned_files'])}개 파일 정리")
        
        return cleanup_info

def main():
    """메타데이터 관리 도구 메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='데이터 메타데이터 관리 도구')
    subparsers = parser.add_subparsers(dest='command', help='사용 가능한 명령어')
    
    # 메타데이터 생성
    create_parser = subparsers.add_parser('create', help='파일 메타데이터 생성')
    create_parser.add_argument('file_path', help='대상 파일 경로')
    create_parser.add_argument('--data_type', default='raw', help='데이터 타입')
    create_parser.add_argument('--tags', nargs='*', help='태그 목록')
    
    # 메타데이터 조회
    get_parser = subparsers.add_parser('get', help='메타데이터 조회')
    get_parser.add_argument('file_path', help='대상 파일 경로')
    
    # 메타데이터 검색
    search_parser = subparsers.add_parser('search', help='메타데이터 검색')
    search_parser.add_argument('--data_type', help='데이터 타입 필터')
    search_parser.add_argument('--collection_type', help='수집 타입 필터')
    search_parser.add_argument('--tags', nargs='*', help='태그 필터')
    search_parser.add_argument('--min_quality', type=float, help='최소 품질 점수')
    
    # 카탈로그 생성
    catalog_parser = subparsers.add_parser('catalog', help='데이터 카탈로그 생성')
    catalog_parser.add_argument('--output', help='출력 파일 경로')
    
    # 정리
    subparsers.add_parser('cleanup', help='고아 메타데이터 정리')
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    metadata_manager = MetadataManager()
    
    try:
        if args.command == 'create':
            metadata = metadata_manager.create_file_metadata(
                args.file_path, 
                data_type=args.data_type,
                tags=args.tags
            )
            print(f"메타데이터 생성 완료: {args.file_path}")
            
        elif args.command == 'get':
            metadata = metadata_manager.get_file_metadata(args.file_path)
            if metadata:
                print(json.dumps(metadata, ensure_ascii=False, indent=2, default=str))
            else:
                print(f"메타데이터를 찾을 수 없습니다: {args.file_path}")
                
        elif args.command == 'search':
            results = metadata_manager.search_metadata(
                data_type=args.data_type,
                collection_type=args.collection_type,
                tags=args.tags,
                min_quality_score=args.min_quality
            )
            print(f"검색 결과: {len(results)}개 파일")
            for result in results:
                print(f"  - {result['file_path']} ({result['data_type']})")
                
        elif args.command == 'catalog':
            catalog = metadata_manager.generate_data_catalog(args.output)
            print(f"데이터 카탈로그 생성 완료")
            print(f"총 파일 수: {catalog['total_files']}")
            print(f"총 크기: {catalog['size_summary']['total_size_bytes']/1024/1024:.1f}MB")
            
        elif args.command == 'cleanup':
            cleanup_info = metadata_manager.cleanup_orphaned_metadata()
            print(f"고아 메타데이터 정리 완료: {len(cleanup_info['cleaned_files'])}개 파일")
            
    except Exception as e:
        print(f"명령 실행 실패: {e}")

if __name__ == "__main__":
    main()
