"""
数据模型定义
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/backup.db")

# 确保data目录存在
os.makedirs("data", exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    tasks = relationship("BackupTask", back_populates="owner")


class BackupTask(Base):
    """备份任务表"""
    __tablename__ = "backup_tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    source_path = Column(String(500))
    backup_type = Column(String(20), default="full")  # full/incremental
    format = Column(String(10), default="tar.gz")  # tar.gz/zip
    is_encrypted = Column(Boolean, default=False)
    schedule = Column(String(50), nullable=True)  # Cron表达式
    is_active = Column(Boolean, default=True)
    status = Column(String(20), default="idle")  # idle/running/paused/completed/failed
    progress = Column(Integer, default=0)  # 0-100
    current_file = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="tasks")
    backups = relationship("BackupFile", back_populates="task")


class BackupFile(Base):
    """备份文件表"""
    __tablename__ = "backup_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255))
    filepath = Column(String(500))
    size = Column(Integer)  # 字节
    backup_type = Column(String(20))  # full/incremental
    checksum_md5 = Column(String(32))
    checksum_sha256 = Column(String(64))
    is_encrypted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    task_id = Column(Integer, ForeignKey("backup_tasks.id"))
    task = relationship("BackupTask", back_populates="backups")


class OperationLog(Base):
    """操作日志表"""
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(50))  # backup/restore/delete/login等
    target = Column(String(255))
    status = Column(String(20))  # success/failed
    message = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    user_id = Column(Integer, ForeignKey("users.id"))


# 创建所有表
Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
