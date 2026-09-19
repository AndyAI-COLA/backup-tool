#!/usr/bin/env python3
"""
测试备份工具
"""

import os
import shutil
from pathlib import Path
from backup_tool import BackupTool

def test_backup():
    """测试备份功能"""
    print("="*50)
    print("测试备份工具")
    print("="*50)

    # 创建测试目录
    test_dir = Path("./test_data")
    test_dir.mkdir(exist_ok=True)

    # 创建测试文件
    for i in range(5):
        (test_dir / f"test_file_{i}.txt").write_text(f"这是测试文件 {i}\n" * 10)

    # 初始化工具
    tool = BackupTool()

    # 测试全量备份
    print("\n1. 测试全量备份...")
    result = tool.backup(source="./test_data", backup_type="full")
    if result:
        print(f"[OK] 全量备份成功: {result.name}")
    else:
        print("[FAIL] 全量备份失败")
        return

    # 测试列出备份
    print("\n2. 测试列出备份...")
    tool.list_backups()

    # 测试验证备份
    print("\n3. 测试验证备份...")
    is_valid = tool.verify()
    if is_valid:
        print("[OK] 验证通过")
    else:
        print("[FAIL] 验证失败")

    # 测试增量备份
    print("\n4. 测试增量备份...")
    # 修改一个文件
    (test_dir / "test_file_0.txt").write_text("修改后的文件\n" * 20)
    result = tool.backup(source="./test_data", backup_type="incremental")
    if result:
        print(f"[OK] 增量备份成功: {result.name}")
    else:
        print("[FAIL] 增量备份失败")

    # 清理测试文件
    print("\n5. 清理测试文件...")
    shutil.rmtree(test_dir, ignore_errors=True)
    print("[OK] 清理完成")

    print("\n" + "="*50)
    print("所有测试完成!")
    print("="*50)

if __name__ == '__main__':
    test_backup()
