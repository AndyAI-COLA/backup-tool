#!/usr/bin/env python3
"""
数据备份恢复工具 v2.0
支持全量备份、增量备份、加密备份、远程备份、定时备份、验证恢复功能
"""

import os
import sys
import json
import tarfile
import zipfile
import shutil
import hashlib
import argparse
import yaml
import logging
import getpass
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from abc import ABC, abstractmethod

# 可选依赖
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
    import base64
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False


class Logger:
    """日志管理器"""

    def __init__(self, log_dir: str = './logs'):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logger()

    def _setup_logger(self):
        """配置日志"""
        self.logger = logging.getLogger('backup_tool')
        self.logger.setLevel(logging.DEBUG)

        # 文件处理器
        log_file = self.log_dir / f"backup_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 格式
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def info(self, msg: str):
        self.logger.info(msg)

    def error(self, msg: str):
        self.logger.error(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def debug(self, msg: str):
        self.logger.debug(msg)


class SensitiveDataMasker:
    """敏感数据脱敏器"""

    SENSITIVE_KEYS = {
        'password', 'passwd', 'secret', 'token', 'api_key',
        'apikey', 'access_key', 'private_key', 'credentials'
    }

    @classmethod
    def mask_dict(cls, data: Dict) -> Dict:
        """脱敏字典中的敏感数据"""
        masked = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in cls.SENSITIVE_KEYS):
                if isinstance(value, str) and len(value) > 4:
                    masked[key] = value[:2] + '*' * (len(value) - 4) + value[-2:]
                else:
                    masked[key] = '****'
            elif isinstance(value, dict):
                masked[key] = cls.mask_dict(value)
            else:
                masked[key] = value
        return masked

    @classmethod
    def mask_config(cls, config: Dict) -> Dict:
        """脱敏配置文件"""
        return cls.mask_dict(config)


class EncryptionManager:
    """加密管理器"""

    def __init__(self, password: str = None):
        if not CRYPTO_AVAILABLE:
            raise ImportError("加密功能需要安装 cryptography: pip install cryptography")
        self.password = password
        self._key = None

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """从密码派生密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt_file(self, input_path: Path, output_path: Path) -> bool:
        """加密文件"""
        try:
            salt = os.urandom(16)
            key = self._derive_key(self.password, salt)
            fernet = Fernet(key)

            with open(input_path, 'rb') as f:
                data = f.read()

            encrypted = fernet.encrypt(data)

            with open(output_path, 'wb') as f:
                f.write(salt + encrypted)

            return True
        except Exception as e:
            print(f"加密失败: {e}")
            return False

    def decrypt_file(self, input_path: Path, output_path: Path) -> bool:
        """解密文件"""
        try:
            with open(input_path, 'rb') as f:
                salt = f.read(16)
                encrypted = f.read()

            key = self._derive_key(self.password, salt)
            fernet = Fernet(key)
            decrypted = fernet.decrypt(encrypted)

            with open(output_path, 'wb') as f:
                f.write(decrypted)

            return True
        except Exception as e:
            print(f"解密失败: {e}")
            return False


class RemoteBackupManager:
    """远程备份管理器（SFTP）"""

    def __init__(self, config: Dict):
        self.config = config.get('remote', {})
        self.enabled = self.config.get('enabled', False)

    def upload(self, local_path: Path) -> bool:
        """上传备份到远程服务器"""
        if not self.enabled:
            return True

        if not PARAMIKO_AVAILABLE:
            print("警告: 远程备份需要安装 paramiko: pip install paramiko")
            return False

        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # 连接
            port = self.config.get('port', 22)
            username = self.config.get('username')
            password = self.config.get('password')
            host = self.config.get('host')

            if not all([host, username]):
                print("错误: 远程备份配置不完整")
                return False

            ssh.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                key_filename=self.config.get('key_file')
            )

            # 上传
            sftp = ssh.open_sftp()
            remote_path = f"{self.config.get('remote_path', '/backups')}/{local_path.name}"
            sftp.put(str(local_path), remote_path)

            sftp.close()
            ssh.close()

            print(f"已上传到远程: {remote_path}")
            return True

        except Exception as e:
            print(f"远程备份失败: {e}")
            return False

    def download(self, remote_name: str, local_dir: Path) -> Optional[Path]:
        """从远程服务器下载备份"""
        if not self.enabled or not PARAMIKO_AVAILABLE:
            return None

        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            ssh.connect(
                hostname=self.config.get('host'),
                port=self.config.get('port', 22),
                username=self.config.get('username'),
                password=self.config.get('password'),
                key_filename=self.config.get('key_file')
            )

            sftp = ssh.open_sftp()
            remote_path = f"{self.config.get('remote_path', '/backups')}/{remote_name}"
            local_path = local_dir / remote_name

            sftp.get(remote_path, str(local_path))

            sftp.close()
            ssh.close()

            return local_path

        except Exception as e:
            print(f"远程下载失败: {e}")
            return None


class BackupVerifier:
    """备份验证器"""

    @staticmethod
    def calculate_checksum(filepath: Path, algorithm: str = 'sha256') -> str:
        """计算文件校验和"""
        if algorithm == 'md5':
            hash_obj = hashlib.md5()
        else:
            hash_obj = hashlib.sha256()

        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_obj.update(chunk)

        return hash_obj.hexdigest()

    @staticmethod
    def verify_backup(backup_path: Path, manifest_path: Path) -> Tuple[bool, str]:
        """
        验证备份完整性

        Returns:
            (是否有效, 验证信息)
        """
        try:
            # 检查备份文件是否存在
            if not backup_path.exists():
                return False, "备份文件不存在"

            # 加载清单
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            # 验证文件大小
            actual_size = backup_path.stat().st_size
            expected_size = manifest.get('archive_size', 0)

            if expected_size > 0 and actual_size != expected_size:
                return False, f"文件大小不匹配: 期望 {expected_size}, 实际 {actual_size}"

            # 验证压缩包完整性
            if backup_path.name.endswith('.tar.gz'):
                with tarfile.open(backup_path, 'r:gz') as tar:
                    members = tar.getmembers()
                    if len(members) != manifest.get('file_count', 0):
                        return False, f"文件数量不匹配: 期望 {manifest.get('file_count')}, 实际 {len(members)}"
            elif backup_path.name.endswith('.zip'):
                with zipfile.ZipFile(backup_path, 'r') as zf:
                    if zf.testzip() is not None:
                        return False, "ZIP文件损坏"

            # 验证校验和（如果清单中包含）
            if 'checksum_sha256' in manifest:
                actual_checksum = BackupVerifier.calculate_checksum(backup_path, 'sha256')
                if actual_checksum != manifest['checksum_sha256']:
                    return False, "SHA256校验和不匹配"

            return True, "验证通过"

        except Exception as e:
            return False, f"验证失败: {str(e)}"


class BackupTool:
    """备份恢复工具类"""

    # 默认排除目录
    DEFAULT_EXCLUDES = [
        'node_modules', '__pycache__', '.git', '.svn',
        'venv', '.venv', 'env', '.env',
        '*.pyc', '*.pyo', '*.pyd',
        '.DS_Store', 'Thumbs.db',
    ]

    def __init__(self, config_path: str = 'backup_config.yaml'):
        """初始化工具"""
        self.config = self._load_config(config_path)
        self.backup_dir = Path(self.config.get('backup_dir', './backups'))
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_dir = self.backup_dir / 'manifests'
        self.manifest_dir.mkdir(exist_ok=True)

        # 初始化组件
        self.logger = Logger(self.config.get('log_dir', './logs'))
        self.remote_manager = RemoteBackupManager(self.config)
        self.verifier = BackupVerifier()

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            self.logger.warning(f"配置文件 {config_path} 不存在，使用默认配置")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'backup_dir': './backups',
            'sources': ['./data'],
            'format': 'tar.gz',
            'exclude': self.DEFAULT_EXCLUDES,
            'max_backups': 10,
            'check_disk_space': True,
            'min_disk_space_gb': 1,
            'encryption': {'enabled': False},
            'remote': {'enabled': False},
            'schedule': {'enabled': False},
            'retention': {'keep_last_n': 10, 'keep_days': 30},
        }

    def _should_exclude(self, path: Path, excludes: List[str]) -> bool:
        """检查路径是否应该排除"""
        for pattern in excludes:
            if pattern.startswith('*'):
                if path.match(pattern):
                    return True
            elif pattern in path.parts or path.name == pattern:
                return True
            for part in path.parts:
                if part == pattern or (pattern.startswith('*') and path.match(pattern)):
                    return True
        return False

    def _get_file_list(self, source: str, excludes: List[str]) -> List[Path]:
        """获取要备份的文件列表"""
        source_path = Path(source)
        if not source_path.exists():
            self.logger.warning(f"源目录 {source} 不存在")
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

    def _check_disk_space(self, source: str, min_space_gb: float = 1) -> bool:
        """检查磁盘空间"""
        try:
            usage = shutil.disk_usage(source)
            free_gb = usage.free / (1024 ** 3)
            total_gb = usage.total / (1024 ** 3)
            used_gb = usage.used / (1024 ** 3)

            self.logger.info(f"磁盘空间检查:")
            self.logger.info(f"  总容量: {total_gb:.2f} GB")
            self.logger.info(f"  已使用: {used_gb:.2f} GB ({usage.used/usage.total*100:.1f}%)")
            self.logger.info(f"  剩余空间: {free_gb:.2f} GB")

            if free_gb < min_space_gb:
                self.logger.warning(f"剩余空间不足 {min_space_gb} GB！")
                return False
            return True
        except Exception as e:
            self.logger.error(f"检查磁盘空间时出错: {e}")
            return True

    def _calculate_total_size(self, files: List[Path]) -> int:
        """计算文件总大小"""
        total = 0
        for f in files:
            if f.exists():
                total += f.stat().st_size
        return total

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"

    def _generate_manifest(self, backup_name: str, backup_type: str,
                          files: List[Path], source: str,
                          archive_path: Path) -> Dict:
        """生成备份清单"""
        total_size = self._calculate_total_size(files)
        archive_size = archive_path.stat().st_size if archive_path.exists() else 0

        manifest = {
            'name': backup_name,
            'type': backup_type,
            'created_at': datetime.now().isoformat(),
            'source': source,
            'file_count': len(files),
            'total_size': total_size,
            'total_size_human': self._format_size(total_size),
            'archive_size': archive_size,
            'archive_size_human': self._format_size(archive_size),
            'checksum_md5': '',
            'checksum_sha256': '',
            'files': [],
        }

        # 计算备份文件校验和
        if archive_path.exists():
            manifest['checksum_md5'] = BackupVerifier.calculate_checksum(archive_path, 'md5')
            manifest['checksum_sha256'] = BackupVerifier.calculate_checksum(archive_path, 'sha256')

        for f in files:
            try:
                file_info = {
                    'path': str(f.relative_to(Path(source).parent)),
                    'size': f.stat().st_size,
                    'mtime': datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                    'md5': self._calculate_file_hash(f, 'md5'),
                    'sha256': self._calculate_file_hash(f, 'sha256'),
                }
                manifest['files'].append(file_info)
            except Exception as e:
                self.logger.warning(f"无法获取文件 {f} 的信息: {e}")

        # 保存清单
        manifest_path = self.manifest_dir / f"{backup_name}_manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        return manifest

    def _get_latest_manifest(self) -> Optional[Dict]:
        """获取最新的备份清单"""
        manifests = list(self.manifest_dir.glob('*_manifest.json'))
        if not manifests:
            return None

        latest = max(manifests, key=lambda x: x.stat().st_mtime)
        with open(latest, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _create_tar_gz(self, backup_path: Path, files: List[Path], base_dir: Path) -> bool:
        """创建tar.gz压缩包"""
        try:
            with tarfile.open(backup_path, 'w:gz') as tar:
                for file_path in files:
                    arcname = file_path.relative_to(base_dir)
                    tar.add(file_path, arcname=arcname)
            return True
        except Exception as e:
            self.logger.error(f"创建tar.gz失败: {e}")
            return False

    def _create_zip(self, backup_path: Path, files: List[Path], base_dir: Path) -> bool:
        """创建zip压缩包"""
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in files:
                    arcname = file_path.relative_to(base_dir)
                    zf.write(file_path, arcname)
            return True
        except Exception as e:
            self.logger.error(f"创建zip失败: {e}")
            return False

    def _cleanup_old_backups(self):
        """清理旧备份，支持保留策略"""
        retention = self.config.get('retention', {})
        keep_last_n = retention.get('keep_last_n', 10)
        keep_days = retention.get('keep_days', 30)

        backup_files = self._get_backup_files()

        if not backup_files:
            return

        # 按时间排序（最新在前）
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        files_to_delete = []

        # 策略1: 保留最近N个
        if len(backup_files) > keep_last_n:
            files_to_delete.extend(backup_files[keep_last_n:])

        # 策略2: 删除超过N天的
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        for f in backup_files:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if mtime < cutoff_date and f not in files_to_delete:
                files_to_delete.append(f)

        # 执行删除
        if files_to_delete:
            self.logger.info(f"清理旧备份: 保留最近 {keep_last_n} 个，保留 {keep_days} 天内")
            for old_backup in files_to_delete:
                self.logger.info(f"  删除: {old_backup.name}")
                old_backup.unlink()
                # 删除对应清单
                manifest_path = self.manifest_dir / f"{old_backup.stem}_manifest.json"
                if manifest_path.exists():
                    manifest_path.unlink()

    def _get_backup_files(self) -> List[Path]:
        """获取所有备份文件"""
        backup_files = []
        for f in self.backup_dir.iterdir():
            if f.is_file() and (f.suffix == '.gz' or f.suffix == '.zip'
                                 or f.name.endswith('.tar.gz')
                                 or f.name.endswith('.enc')):
                backup_files.append(f)
        return backup_files

    def backup(self, source: str = None, backup_type: str = 'full',
               format: str = None, excludes: List[str] = None,
               encrypt: bool = False, password: str = None) -> Optional[Path]:
        """
        执行备份

        Args:
            source: 源目录路径
            backup_type: 备份类型 (full/incremental)
            format: 压缩格式 (tar.gz/zip)
            excludes: 额外排除的文件模式
            encrypt: 是否加密
            password: 加密密码

        Returns:
            备份文件路径，失败返回None
        """
        self.logger.info("="*50)
        self.logger.info("开始备份任务")
        self.logger.info("="*50)

        # 加密配置
        encryption_config = self.config.get('encryption', {})
        if encrypt or encryption_config.get('enabled', False):
            if not password:
                password = encryption_config.get('password')
            if not password:
                password = getpass.getpass("请输入加密密码: ")
            if not CRYPTO_AVAILABLE:
                self.logger.error("加密功能需要安装 cryptography: pip install cryptography")
                return None

        # 确定源目录
        if source:
            sources = [source]
        else:
            sources = self.config.get('sources', [])

        if not sources:
            self.logger.error("未指定备份源目录")
            return None

        # 确定格式
        if not format:
            format = self.config.get('format', 'tar.gz')

        # 合并排除规则
        all_excludes = self.DEFAULT_EXCLUDES.copy()
        if excludes:
            all_excludes.extend(excludes)
        config_excludes = self.config.get('exclude', [])
        if config_excludes:
            all_excludes.extend(config_excludes)

        # 检查磁盘空间
        if self.config.get('check_disk_space', True):
            if not self._check_disk_space(sources[0],
                                          self.config.get('min_disk_space_gb', 1)):
                self.logger.error("磁盘空间不足，备份中止")
                return None

        # 收集文件
        all_files = []
        for src in sources:
            files = self._get_file_list(src, all_excludes)
            all_files.extend(files)

        if not all_files:
            self.logger.warning("没有找到需要备份的文件")
            return None

        # 增量备份处理
        if backup_type == 'incremental':
            latest_manifest = self._get_latest_manifest()
            if latest_manifest:
                latest_hashes = {f['md5'] for f in latest_manifest.get('files', [])}
                changed_files = []
                for f in all_files:
                    file_hash = self._calculate_file_hash(f)
                    if file_hash not in latest_hashes:
                        changed_files.append(f)
                all_files = changed_files
                self.logger.info(f"增量备份: 发现 {len(all_files)} 个变更文件")
            else:
                self.logger.info("未找到之前的备份，执行全量备份")
                backup_type = 'full'

        if not all_files:
            self.logger.info("没有变更的文件，无需备份")
            return None

        # 生成备份名称
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{timestamp}"

        # 确定基础目录
        base_dir = Path(sources[0])
        if len(sources) > 1:
            base_dir = Path(os.path.commonpath(sources))

        # 创建备份
        backup_path = self.backup_dir / f"{backup_name}.{'zip' if format == 'zip' else 'tar.gz'}"

        if format == 'tar.gz':
            success = self._create_tar_gz(backup_path, all_files, base_dir)
        elif format == 'zip':
            success = self._create_zip(backup_path, all_files, base_dir)
        else:
            self.logger.error(f"不支持的格式: {format}")
            return None

        if not success:
            return None

        # 加密处理
        if password:
            encrypted_path = self.backup_dir / f"{backup_name}.enc"
            if EncryptionManager(password).encrypt_file(backup_path, encrypted_path):
                backup_path.unlink()
                backup_path = encrypted_path
                self.logger.info("备份已加密")

        # 生成清单
        manifest = self._generate_manifest(backup_name, backup_type,
                                           all_files, str(base_dir), backup_path)

        # 打印结果
        self.logger.info("="*50)
        self.logger.info("备份完成!")
        self.logger.info("="*50)
        self.logger.info(f"备份文件: {backup_path.name}")
        self.logger.info(f"备份类型: {backup_type}")
        self.logger.info(f"文件数量: {manifest['file_count']}")
        self.logger.info(f"原始大小: {manifest['total_size_human']}")
        self.logger.info(f"压缩大小: {manifest['archive_size_human']}")
        self.logger.info(f"MD5: {manifest['checksum_md5'][:16]}...")
        self.logger.info(f"SHA256: {manifest['checksum_sha256'][:16]}...")
        self.logger.info(f"创建时间: {manifest['created_at']}")
        self.logger.info("="*50)

        # 远程备份
        if self.remote_manager.enabled:
            self.remote_manager.upload(backup_path)

        # 清理旧备份
        self._cleanup_old_backups()

        return backup_path

    def verify(self, backup_name: str = None) -> bool:
        """
        验证备份完整性

        Args:
            backup_name: 备份名称，不指定则验证最新备份

        Returns:
            验证是否通过
        """
        self.logger.info("开始验证备份完整性...")

        if backup_name:
            # 查找指定备份
            backup_path = self._find_backup(backup_name)
            if not backup_path:
                self.logger.error(f"找不到备份: {backup_name}")
                return False
            manifest_path = self.manifest_dir / f"{backup_name}_manifest.json"
        else:
            # 验证最新备份
            backup_files = self._get_backup_files()
            if not backup_files:
                self.logger.error("没有找到备份文件")
                return False
            backup_path = max(backup_files, key=lambda x: x.stat().st_mtime)
            # 处理.tar.gz格式的文件名
            if backup_path.name.endswith('.tar.gz'):
                backup_name_clean = backup_path.name[:-7]  # 移除.tar.gz
            else:
                backup_name_clean = backup_path.stem
            manifest_path = self.manifest_dir / f"{backup_name_clean}_manifest.json"

        if not manifest_path.exists():
            self.logger.error(f"清单文件不存在: {manifest_path.name}")
            return False

        is_valid, message = BackupVerifier.verify_backup(backup_path, manifest_path)

        if is_valid:
            self.logger.info(f"验证通过: {message}")
        else:
            self.logger.error(f"验证失败: {message}")

        return is_valid

    def _find_backup(self, backup_name: str) -> Optional[Path]:
        """查找备份文件"""
        for ext in ['.tar.gz', '.zip', '.gz', '.enc']:
            path = self.backup_dir / f"{backup_name}{ext}"
            if path.exists():
                return path

        # 尝试部分匹配
        for f in self.backup_dir.iterdir():
            if backup_name in f.name:
                return f
        return None

    def list_backups(self):
        """列出所有备份"""
        backup_files = self._get_backup_files()
        if not backup_files:
            self.logger.info("没有找到任何备份文件")
            return

        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        print(f"\n{'='*80}")
        print(f"{'备份列表':^76}")
        print(f"{'='*80}")
        print(f"{'序号':<5} {'文件名':<35} {'大小':<12} {'创建时间':<25}")
        print(f"{'-'*80}")

        for idx, backup in enumerate(backup_files, 1):
            size = self._format_size(backup.stat().st_size)
            mtime = datetime.fromtimestamp(backup.stat().st_mtime).strftime(
                '%Y-%m-%d %H:%M:%S')
            print(f"{idx:<5} {backup.name:<35} {size:<12} {mtime:<25}")

        print(f"{'='*80}")
        print(f"共 {len(backup_files)} 个备份\n")

    def show_manifest(self, backup_name: str = None):
        """显示备份清单"""
        if backup_name:
            manifest_path = self.manifest_dir / f"{backup_name}_manifest.json"
        else:
            manifests = list(self.manifest_dir.glob('*_manifest.json'))
            if not manifests:
                self.logger.info("没有找到任何备份清单")
                return
            manifest_path = max(manifests, key=lambda x: x.stat().st_mtime)

        if not manifest_path.exists():
            self.logger.error(f"清单 {manifest_path.name} 不存在")
            return

        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        print(f"\n{'='*60}")
        print(f"备份清单: {manifest['name']}")
        print(f"{'='*60}")
        print(f"备份类型: {manifest['type']}")
        print(f"创建时间: {manifest['created_at']}")
        print(f"源目录: {manifest['source']}")
        print(f"文件数量: {manifest['file_count']}")
        print(f"原始大小: {manifest['total_size_human']}")
        print(f"压缩大小: {manifest['archive_size_human']}")
        print(f"MD5: {manifest.get('checksum_md5', 'N/A')}")
        print(f"SHA256: {manifest.get('checksum_sha256', 'N/A')}")
        print(f"{'-'*60}")
        print("文件列表:")
        for file_info in manifest.get('files', []):
            size = self._format_size(file_info['size'])
            print(f"  {file_info['path']} ({size})")
        print(f"{'='*60}\n")

    def restore(self, backup_name: str, restore_path: str = None,
                password: str = None) -> bool:
        """
        恢复备份

        Args:
            backup_name: 备份名称
            restore_path: 恢复路径
            password: 解密密码

        Returns:
            是否成功
        """
        self.logger.info("开始恢复备份...")

        # 查找备份文件
        backup_path = self._find_backup(backup_name)
        if not backup_path:
            self.logger.error(f"找不到备份: {backup_name}")
            return False

        # 确定恢复路径
        if restore_path:
            restore_dir = Path(restore_path)
        else:
            restore_dir = Path('.')
        restore_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"恢复备份: {backup_path.name}")
        self.logger.info(f"恢复到: {restore_dir.absolute()}")

        try:
            # 处理加密文件
            if backup_path.name.endswith('.enc'):
                if not password:
                    encryption_config = self.config.get('encryption', {})
                    password = encryption_config.get('password')
                if not password:
                    password = getpass.getpass("请输入解密密码: ")

                # 解密到临时文件
                temp_path = self.backup_dir / "temp_restore"
                if EncryptionManager(password).decrypt_file(backup_path, temp_path):
                    backup_path = temp_path
                else:
                    self.logger.error("解密失败")
                    return False

            # 解压
            if backup_path.name.endswith('.tar.gz'):
                with tarfile.open(backup_path, 'r:gz') as tar:
                    members = tar.getmembers()
                    self.logger.info(f"包含 {len(members)} 个文件/目录")
                    tar.extractall(path=restore_dir)
            elif backup_path.name.endswith('.zip'):
                with zipfile.ZipFile(backup_path, 'r') as zf:
                    members = zf.namelist()
                    self.logger.info(f"包含 {len(members)} 个文件/目录")
                    zf.extractall(path=restore_dir)
            else:
                self.logger.error(f"不支持的备份格式: {backup_path.suffix}")
                return False

            self.logger.info("恢复成功!")
            return True

        except Exception as e:
            self.logger.error(f"恢复失败: {e}")
            return False

    def delete(self, backup_name: str) -> bool:
        """删除指定备份"""
        backup_path = self._find_backup(backup_name)
        if not backup_path:
            self.logger.error(f"找不到备份: {backup_name}")
            return False

        self.logger.info(f"删除备份: {backup_path.name}")
        backup_path.unlink()

        manifest_path = self.manifest_dir / f"{backup_name}_manifest.json"
        if manifest_path.exists():
            manifest_path.unlink()

        self.logger.info("删除成功!")
        return True

    def schedule_backup(self, interval: str = 'daily', time: str = '02:00',
                       backup_type: str = 'full'):
        """
        设置定时备份

        Args:
            interval: 间隔 (hourly/daily/weekly/monthly)
            time: 执行时间
            backup_type: 备份类型
        """
        if not SCHEDULE_AVAILABLE:
            self.logger.error("定时备份需要安装 schedule: pip install schedule")
            return

        def job():
            self.logger.info(f"执行定时备份 ({backup_type})")
            self.backup(backup_type=backup_type)

        if interval == 'hourly':
            schedule.every().hour.at(time).do(job)
        elif interval == 'daily':
            schedule.every().day.at(time).do(job)
        elif interval == 'weekly':
            schedule.every().week.at(time).do(job)
        elif interval == 'monthly':
            schedule.every(30).days.at(time).do(job)

        self.logger.info(f"定时备份已设置: {interval} at {time}")

        while True:
            schedule.run_pending()
            import time
            time.sleep(60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='数据备份恢复工具 v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  %(prog)s backup                              # 全量备份
  %(prog)s backup -t incremental               # 增量备份
  %(prog)s backup -s /path/to/dir              # 备份指定目录
  %(prog)s backup -f zip                       # 使用zip格式
  %(prog)s backup --encrypt                    # 加密备份
  %(prog)s list                                # 列出所有备份
  %(prog)s verify                              # 验证最新备份
  %(prog)s verify backup_20240101_120000       # 验证指定备份
  %(prog)s manifest                            # 显示最新备份清单
  %(prog)s restore backup_20240101_120000      # 恢复指定备份
  %(prog)s delete backup_20240101_120000       # 删除指定备份
  %(prog)s schedule --interval daily --time 02:00  # 设置定时备份
        ''')

    parser.add_argument('-c', '--config', default='backup_config.yaml',
                       help='配置文件路径 (默认: backup_config.yaml)')

    subparsers = parser.add_subparsers(dest='command', help='命令')

    # backup 命令
    backup_parser = subparsers.add_parser('backup', help='创建备份')
    backup_parser.add_argument('-s', '--source', help='源目录路径')
    backup_parser.add_argument('-t', '--type', choices=['full', 'incremental'],
                              default='full', help='备份类型 (默认: full)')
    backup_parser.add_argument('-f', '--format', choices=['tar.gz', 'zip'],
                              help='压缩格式')
    backup_parser.add_argument('-e', '--exclude', nargs='*',
                              help='额外排除的文件模式')
    backup_parser.add_argument('--encrypt', action='store_true',
                              help='加密备份')
    backup_parser.add_argument('-p', '--password', help='加密密码')

    # list 命令
    subparsers.add_parser('list', help='列出所有备份')

    # verify 命令
    verify_parser = subparsers.add_parser('verify', help='验证备份完整性')
    verify_parser.add_argument('-n', '--name', help='备份名称')

    # manifest 命令
    manifest_parser = subparsers.add_parser('manifest', help='显示备份清单')
    manifest_parser.add_argument('-n', '--name', help='备份名称')

    # restore 命令
    restore_parser = subparsers.add_parser('restore', help='恢复备份')
    restore_parser.add_argument('backup_name', help='备份名称')
    restore_parser.add_argument('-p', '--path', help='恢复路径')
    restore_parser.add_argument('--password', help='解密密码')

    # delete 命令
    delete_parser = subparsers.add_parser('delete', help='删除备份')
    delete_parser.add_argument('backup_name', help='备份名称')

    # schedule 命令
    schedule_parser = subparsers.add_parser('schedule', help='设置定时备份')
    schedule_parser.add_argument('-i', '--interval', default='daily',
                               choices=['hourly', 'daily', 'weekly', 'monthly'],
                               help='备份间隔 (默认: daily)')
    schedule_parser.add_argument('-t', '--time', default='02:00',
                               help='执行时间 (默认: 02:00)')
    schedule_parser.add_argument('--type', default='full',
                               choices=['full', 'incremental'],
                               help='备份类型')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 初始化工具
    tool = BackupTool(args.config)

    # 执行命令
    if args.command == 'backup':
        tool.backup(
            source=args.source,
            backup_type=args.type,
            format=args.format,
            excludes=args.exclude,
            encrypt=args.encrypt,
            password=args.password
        )
    elif args.command == 'list':
        tool.list_backups()
    elif args.command == 'verify':
        tool.verify(args.name)
    elif args.command == 'manifest':
        tool.show_manifest(args.name)
    elif args.command == 'restore':
        tool.restore(args.backup_name, args.path, args.password)
    elif args.command == 'delete':
        tool.delete(args.backup_name)
    elif args.command == 'schedule':
        tool.schedule_backup(args.interval, args.time, args.type)


if __name__ == '__main__':
    main()
