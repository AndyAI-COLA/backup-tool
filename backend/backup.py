"""
备份核心逻辑
"""

import os
import hashlib
import tarfile
import zipfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Callable
import json


class BackupEngine:
    """备份引擎"""

    # 默认排除目录
    DEFAULT_EXCLUDES = [
        'node_modules', '__pycache__', '.git', '.svn',
        'venv', '.venv', 'env', '.env',
        '*.pyc', '*.pyo', '*.pyd',
        '.DS_Store', 'Thumbs.db',
    ]

    def __init__(self, backup_dir: str = './backups'):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_dir = self.backup_dir / 'manifests'
        self.manifest_dir.mkdir(exist_ok=True)

    def _should_exclude(self, path: Path, excludes: List[str]) -> bool:
        """检查路径是否应该排除"""
        for pattern in excludes:
            if pattern.startswith('*'):
                if path.match(pattern):
                    return True
            elif pattern in path.parts or path.name == pattern:
                return True
            for part in path.parts:
                if part == pattern:
                    return True
        return False

    def _get_file_list(self, source: str, excludes: List[str]) -> List[Path]:
        """获取要备份的文件列表"""
        source_path = Path(source)
        if not source_path.exists():
            return []

        files = []
        if source_path.is_file():
            return [source_path]

        for item in source_path.rglob('*'):
            if item.is_file() and not self._should_exclude(item, excludes):
                files.append(item)
        return sorted(files)

    def _calculate_file_hash(self, filepath: Path, algorithm: str = 'md5') -> str:
        """计算文件哈希值"""
        if algorithm == 'sha256':
            hash_obj = hashlib.sha256()
        else:
            hash_obj = hashlib.md5()

        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"

    def create_backup(
        self,
        source: str,
        backup_type: str = 'full',
        format: str = 'tar.gz',
        excludes: List[str] = None,
        progress_callback: Callable = None
    ) -> dict:
        """
        创建备份

        Args:
            source: 源目录
            backup_type: 备份类型 (full/incremental)
            format: 压缩格式 (tar.gz/zip)
            excludes: 排除规则
            progress_callback: 进度回调函数

        Returns:
            备份结果信息
        """
        # 合并排除规则
        all_excludes = self.DEFAULT_EXCLUDES.copy()
        if excludes:
            all_excludes.extend(excludes)

        # 获取文件列表
        files = self._get_file_list(source, all_excludes)
        if not files:
            return {"success": False, "message": "没有找到需要备份的文件"}

        # 生成备份名称
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{timestamp}"

        # 确定基础目录
        base_dir = Path(source)

        # 创建备份
        if format == 'tar.gz':
            backup_path = self.backup_dir / f"{backup_name}.tar.gz"
            success = self._create_tar_gz(backup_path, files, base_dir, progress_callback)
        elif format == 'zip':
            backup_path = self.backup_dir / f"{backup_name}.zip"
            success = self._create_zip(backup_path, files, base_dir, progress_callback)
        else:
            return {"success": False, "message": f"不支持的格式: {format}"}

        if not success:
            return {"success": False, "message": "创建备份失败"}

        # 生成清单
        archive_size = backup_path.stat().st_size
        manifest = {
            'name': backup_name,
            'type': backup_type,
            'created_at': datetime.now().isoformat(),
            'source': source,
            'file_count': len(files),
            'total_size': sum(f.stat().st_size for f in files if f.exists()),
            'archive_size': archive_size,
            'archive_size_human': self._format_size(archive_size),
            'checksum_md5': self._calculate_file_hash(backup_path, 'md5'),
            'checksum_sha256': self._calculate_file_hash(backup_path, 'sha256'),
        }

        # 保存清单
        manifest_path = self.manifest_dir / f"{backup_name}_manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        return {
            "success": True,
            "message": "备份完成",
            "backup_name": backup_name,
            "filename": backup_path.name,
            "file_count": len(files),
            "size": archive_size,
            "size_human": self._format_size(archive_size),
            "checksum_md5": manifest['checksum_md5'],
            "checksum_sha256": manifest['checksum_sha256'],
        }

    def _create_tar_gz(self, backup_path: Path, files: List[Path], base_dir: Path,
                       progress_callback: Callable = None) -> bool:
        """创建tar.gz压缩包"""
        try:
            total = len(files)
            with tarfile.open(backup_path, 'w:gz') as tar:
                for idx, file_path in enumerate(files):
                    arcname = file_path.relative_to(base_dir)
                    tar.add(file_path, arcname=arcname)
                    if progress_callback:
                        progress = int((idx + 1) / total * 100)
                        progress_callback(progress, str(file_path.name))
            return True
        except Exception as e:
            print(f"创建tar.gz失败: {e}")
            return False

    def _create_zip(self, backup_path: Path, files: List[Path], base_dir: Path,
                    progress_callback: Callable = None) -> bool:
        """创建zip压缩包"""
        try:
            total = len(files)
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for idx, file_path in enumerate(files):
                    arcname = file_path.relative_to(base_dir)
                    zf.write(file_path, arcname)
                    if progress_callback:
                        progress = int((idx + 1) / total * 100)
                        progress_callback(progress, str(file_path.name))
            return True
        except Exception as e:
            print(f"创建zip失败: {e}")
            return False

    def restore_backup(self, backup_path: str, restore_path: str) -> dict:
        """
        恢复备份

        Args:
            backup_path: 备份文件路径
            restore_path: 恢复路径

        Returns:
            恢复结果
        """
        backup_file = Path(backup_path)
        if not backup_file.exists():
            return {"success": False, "message": "备份文件不存在"}

        restore_dir = Path(restore_path)
        restore_dir.mkdir(parents=True, exist_ok=True)

        try:
            if backup_file.name.endswith('.tar.gz'):
                with tarfile.open(backup_file, 'r:gz') as tar:
                    tar.extractall(path=restore_dir)
            elif backup_file.name.endswith('.zip'):
                with zipfile.ZipFile(backup_file, 'r') as zf:
                    zf.extractall(path=restore_dir)
            else:
                return {"success": False, "message": "不支持的备份格式"}

            return {"success": True, "message": "恢复完成", "path": str(restore_dir)}
        except Exception as e:
            return {"success": False, "message": f"恢复失败: {str(e)}"}

    def delete_backup(self, backup_name: str) -> dict:
        """删除备份"""
        for ext in ['.tar.gz', '.zip']:
            path = self.backup_dir / f"{backup_name}{ext}"
            if path.exists():
                path.unlink()
                # 删除清单
                manifest_path = self.manifest_dir / f"{backup_name}_manifest.json"
                if manifest_path.exists():
                    manifest_path.unlink()
                return {"success": True, "message": "删除成功"}

        return {"success": False, "message": "未找到备份文件"}

    def list_backups(self) -> List[dict]:
        """列出所有备份"""
        backups = []
        for f in self.backup_dir.iterdir():
            if f.is_file() and (f.suffix == '.gz' or f.suffix == '.zip'
                                 or f.name.endswith('.tar.gz')):
                # 加载清单
                if f.name.endswith('.tar.gz'):
                    manifest_name = f.name[:-7]
                else:
                    manifest_name = f.stem
                manifest_path = self.manifest_dir / f"{manifest_name}_manifest.json"

                info = {
                    "filename": f.name,
                    "size": f.stat().st_size,
                    "size_human": self._format_size(f.stat().st_size),
                    "created_at": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                }

                if manifest_path.exists():
                    with open(manifest_path, 'r', encoding='utf-8') as file:
                        manifest = json.load(file)
                        info.update({
                            "name": manifest.get("name"),
                            "type": manifest.get("type"),
                            "file_count": manifest.get("file_count"),
                            "source": manifest.get("source"),
                            "checksum_md5": manifest.get("checksum_md5"),
                            "checksum_sha256": manifest.get("checksum_sha256"),
                        })

                backups.append(info)

        return sorted(backups, key=lambda x: x.get("created_at", ""), reverse=True)

    def verify_backup(self, backup_name: str) -> dict:
        """验证备份完整性"""
        # 查找备份文件
        backup_path = None
        for ext in ['.tar.gz', '.zip']:
            path = self.backup_dir / f"{backup_name}{ext}"
            if path.exists():
                backup_path = path
                break

        if not backup_path:
            return {"success": False, "message": "未找到备份文件"}

        # 加载清单
        if backup_path.name.endswith('.tar.gz'):
            manifest_name = backup_path.name[:-7]
        else:
            manifest_name = backup_path.stem
        manifest_path = self.manifest_dir / f"{manifest_name}_manifest.json"

        if not manifest_path.exists():
            return {"success": False, "message": "未找到清单文件"}

        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        # 验证校验和
        actual_md5 = self._calculate_file_hash(backup_path, 'md5')
        actual_sha256 = self._calculate_file_hash(backup_path, 'sha256')

        if actual_md5 != manifest.get('checksum_md5'):
            return {"success": False, "message": "MD5校验和不匹配"}
        if actual_sha256 != manifest.get('checksum_sha256'):
            return {"success": False, "message": "SHA256校验和不匹配"}

        return {"success": True, "message": "验证通过", "manifest": manifest}


# 全局备份引擎实例
backup_engine = BackupEngine()
