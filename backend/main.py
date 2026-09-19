"""
数据备份恢复工具 - FastAPI后端
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from jose import jwt
from passlib.context import CryptContext

from models import get_db, User, BackupTask, BackupFile, OperationLog, SessionLocal
from auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, SECRET_KEY, ALGORITHM
)
from backup import backup_engine

# 创建FastAPI应用
app = FastAPI(title="数据备份恢复工具", version="2.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# WebSocket连接管理
active_connections: List[WebSocket] = []


# ============== 数据模型 ==============

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class BackupTaskCreate(BaseModel):
    name: str
    source_path: str
    backup_type: str = "full"
    format: str = "tar.gz"
    is_encrypted: bool = False
    schedule: Optional[str] = None

class BackupTaskUpdate(BaseModel):
    name: Optional[str] = None
    source_path: Optional[str] = None
    backup_type: Optional[str] = None
    format: Optional[str] = None
    schedule: Optional[str] = None


# ============== 认证接口 ==============

@app.post("/api/auth/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 检查邮箱
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    # 创建用户
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()

    # 记录日志
    log = OperationLog(action="register", target=user.username, status="success", user_id=db_user.id)
    db.add(log)
    db.commit()

    return {"message": "注册成功", "user_id": db_user.id}

@app.post("/api/auth/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 创建令牌
    access_token = create_access_token(data={"sub": db_user.username})

    # 记录日志
    log = OperationLog(action="login", target=user.username, status="success", user_id=db_user.id)
    db.add(log)
    db.commit()

    return {"access_token": access_token, "token_type": "bearer", "username": db_user.username}

@app.get("/api/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return {"id": current_user.id, "username": current_user.username, "email": current_user.email}


# ============== 备份任务接口 ==============

@app.get("/api/tasks")
async def list_tasks(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取任务列表"""
    tasks = db.query(BackupTask).filter(BackupTask.owner_id == current_user.id).all()
    return [{"id": t.id, "name": t.name, "source_path": t.source_path, "backup_type": t.backup_type,
             "format": t.format, "status": t.status, "progress": t.progress,
             "current_file": t.current_file, "schedule": t.schedule,
             "created_at": t.created_at.isoformat() if t.created_at else None} for t in tasks]

@app.post("/api/tasks")
async def create_task(task: BackupTaskCreate, current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """创建备份任务"""
    db_task = BackupTask(
        name=task.name,
        source_path=task.source_path,
        backup_type=task.backup_type,
        format=task.format,
        is_encrypted=task.is_encrypted,
        schedule=task.schedule,
        owner_id=current_user.id
    )
    db.add(db_task)
    db.commit()

    # 记录日志
    log = OperationLog(action="create_task", target=task.name, status="success", user_id=current_user.id)
    db.add(log)
    db.commit()

    return {"message": "任务创建成功", "task_id": db_task.id}

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: int, current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """删除备份任务"""
    task = db.query(BackupTask).filter(BackupTask.id == task_id, BackupTask.owner_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    db.delete(task)
    db.commit()

    # 记录日志
    log = OperationLog(action="delete_task", target=task.name, status="success", user_id=current_user.id)
    db.add(log)
    db.commit()

    return {"message": "删除成功"}


# ============== 备份操作接口 ==============

@app.post("/api/backup/execute/{task_id}")
async def execute_backup(task_id: int, current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """执行备份任务"""
    task = db.query(BackupTask).filter(BackupTask.id == task_id, BackupTask.owner_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status == "running":
        raise HTTPException(status_code=400, detail="任务正在运行中")

    # 更新任务状态
    task.status = "running"
    task.progress = 0
    db.commit()

    # 记录日志
    log = OperationLog(action="backup", target=task.name, status="running", user_id=current_user.id)
    db.add(log)
    db.commit()

    # 执行备份（异步）
    async def run_backup():
        def progress_callback(progress, filename):
            task.progress = progress
            task.current_file = filename
            db.commit()
            # 广播进度
            asyncio.create_task(broadcast_progress(task_id, progress, filename))

        try:
            result = backup_engine.create_backup(
                source=task.source_path,
                backup_type=task.backup_type,
                format=task.format,
                progress_callback=progress_callback
            )

            if result["success"]:
                # 保存备份文件记录
                backup_file = BackupFile(
                    filename=result["filename"],
                    filepath=task.source_path,
                    size=result["size"],
                    backup_type=task.backup_type,
                    checksum_md5=result["checksum_md5"],
                    checksum_sha256=result["checksum_sha256"],
                    task_id=task.id
                )
                db.add(backup_file)
                task.status = "completed"
                task.progress = 100
                log.status = "success"
            else:
                task.status = "failed"
                log.status = "failed"
                log.message = result["message"]

            db.commit()
        except Exception as e:
            task.status = "failed"
            log.status = "failed"
            log.message = str(e)
            db.commit()

    asyncio.create_task(run_backup())

    return {"message": "备份任务已启动", "task_id": task_id}


# ============== 备份文件接口 ==============

@app.get("/api/backups")
async def list_backups(current_user: User = Depends(get_current_user)):
    """获取备份文件列表"""
    return backup_engine.list_backups()

@app.get("/api/backups/download/{filename}")
async def download_backup(filename: str, current_user: User = Depends(get_current_user)):
    """下载备份文件"""
    file_path = backup_engine.backup_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path, filename=filename)

@app.get("/api/backups/verify/{backup_name}")
async def verify_backup(backup_name: str, current_user: User = Depends(get_current_user)):
    """验证备份完整性"""
    return backup_engine.verify_backup(backup_name)

@app.delete("/api/backups/{filename}")
async def delete_backup(filename: str, current_user: User = Depends(get_current_user)):
    """删除备份文件"""
    backup_name = filename.replace('.tar.gz', '').replace('.zip', '')
    return backup_engine.delete_backup(backup_name)


# ============== 日志接口 ==============

@app.get("/api/logs")
async def list_logs(limit: int = 100, current_user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """获取操作日志"""
    logs = db.query(OperationLog).filter(
        OperationLog.user_id == current_user.id
    ).order_by(OperationLog.created_at.desc()).limit(limit).all()
    return [{"id": l.id, "action": l.action, "target": l.target,
             "status": l.status, "message": l.message,
             "created_at": l.created_at.isoformat() if l.created_at else None} for l in logs]


# ============== 统计接口 ==============

@app.get("/api/stats")
async def get_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取统计数据"""
    tasks = db.query(BackupTask).filter(BackupTask.owner_id == current_user.id).all()
    backups = db.query(BackupFile).join(BackupTask).filter(BackupTask.owner_id == current_user.id).all()

    total_size = sum(b.size for b in backups if b.size)

    # 按类型统计
    full_count = sum(1 for t in tasks if t.backup_type == "full")
    incremental_count = sum(1 for t in tasks if t.backup_type == "incremental")

    return {
        "total_tasks": len(tasks),
        "total_backups": len(backups),
        "total_size": total_size,
        "total_size_human": backup_engine._format_size(total_size),
        "full_count": full_count,
        "incremental_count": incremental_count,
        "recent_backups": backup_engine.list_backups()[:5]
    }


# ============== WebSocket ==============

@app.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    """WebSocket实时进度推送"""
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def broadcast_progress(task_id: int, progress: int, filename: str):
    """广播进度"""
    message = json.dumps({"task_id": task_id, "progress": progress, "filename": filename})
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except:
            pass


# ============== 静态文件 ==============

# 挂载前端静态文件
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
async def root():
    """返回前端页面"""
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "数据备份恢复工具 API", "docs": "/docs"}

@app.get("/{page}.html")
async def get_page(page: str):
    """返回前端页面"""
    file_path = os.path.join(frontend_path, f"{page}.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="页面不存在")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
