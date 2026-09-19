#!/usr/bin/env python3
"""
数据备份恢复工具 - 图形界面版本
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from pathlib import Path
from backup_tool import BackupTool


class BackupGUI:
    """备份工具图形界面"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("数据备份恢复工具 v2.0")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # 设置主题
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # 初始化工具
        self.tool = BackupTool()

        # 创建界面
        self._create_widgets()

    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)

        # 标题
        title_label = ttk.Label(main_frame, text="📦 数据备份恢复工具",
                               font=('微软雅黑', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # ==================== 备份区域 ====================
        backup_frame = ttk.LabelFrame(main_frame, text="备份操作", padding="10")
        backup_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        backup_frame.columnconfigure(1, weight=1)

        # 源目录选择
        ttk.Label(backup_frame, text="源目录:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.source_var = tk.StringVar(value="./data")
        ttk.Entry(backup_frame, textvariable=self.source_var, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E))
        ttk.Button(backup_frame, text="浏览", command=self._browse_source).grid(row=0, column=2, padx=(10, 0))

        # 备份类型
        ttk.Label(backup_frame, text="备份类型:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.type_var = tk.StringVar(value="full")
        type_frame = ttk.Frame(backup_frame)
        type_frame.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=(10, 0))
        ttk.Radiobutton(type_frame, text="全量备份", variable=self.type_var, value="full").pack(side=tk.LEFT)
        ttk.Radiobutton(type_frame, text="增量备份", variable=self.type_var, value="incremental").pack(side=tk.LEFT, padx=(20, 0))

        # 压缩格式
        ttk.Label(backup_frame, text="压缩格式:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.format_var = tk.StringVar(value="tar.gz")
        format_frame = ttk.Frame(backup_frame)
        format_frame.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=(10, 0))
        ttk.Radiobutton(format_frame, text="tar.gz", variable=self.format_var, value="tar.gz").pack(side=tk.LEFT)
        ttk.Radiobutton(format_frame, text="zip", variable=self.format_var, value="zip").pack(side=tk.LEFT, padx=(20, 0))

        # 加密选项
        self.encrypt_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(backup_frame, text="加密备份", variable=self.encrypt_var).grid(row=3, column=0, sticky=tk.W, pady=(10, 0))
        self.password_var = tk.StringVar()
        ttk.Entry(backup_frame, textvariable=self.password_var, show="*", width=30).grid(row=3, column=1, sticky=tk.W, pady=(10, 0))
        ttk.Label(backup_frame, text="(加密时输入密码)").grid(row=3, column=2, sticky=tk.W, padx=(10, 0), pady=(10, 0))

        # 备份按钮
        backup_btn = ttk.Button(backup_frame, text="开始备份", command=self._start_backup)
        backup_btn.grid(row=4, column=0, columnspan=3, pady=(15, 0))

        # ==================== 操作区域 ====================
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Button(action_frame, text="📋 列出备份", command=self._list_backups).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="✅ 验证备份", command=self._verify_backup).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="📥 恢复备份", command=self._restore_backup).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="🗑️ 删除备份", command=self._delete_backup).pack(side=tk.LEFT)

        # ==================== 日志区域 ====================
        log_frame = ttk.LabelFrame(main_frame, text="操作日志", padding="10")
        log_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=70)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # ==================== 状态栏 ====================
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E))

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(fill=tk.X)

    def _log(self, message: str):
        """添加日志"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def _browse_source(self):
        """浏览源目录"""
        directory = filedialog.askdirectory(title="选择要备份的目录")
        if directory:
            self.source_var.set(directory)

    def _start_backup(self):
        """开始备份"""
        source = self.source_var.get()
        if not source or not Path(source).exists():
            messagebox.showerror("错误", "请选择有效的源目录")
            return

        self.status_var.set("备份中...")
        self._log(f"开始备份: {source}")

        def backup_thread():
            try:
                result = self.tool.backup(
                    source=source,
                    backup_type=self.type_var.get(),
                    format=self.format_var.get(),
                    encrypt=self.encrypt_var.get(),
                    password=self.password_var.get() if self.encrypt_var.get() else None
                )
                if result:
                    self._log(f"✅ 备份完成: {result.name}")
                    messagebox.showinfo("成功", f"备份完成!\n{result.name}")
                else:
                    self._log("❌ 备份失败")
                    messagebox.showerror("错误", "备份失败")
            except Exception as e:
                self._log(f"❌ 错误: {str(e)}")
                messagebox.showerror("错误", str(e))
            finally:
                self.status_var.set("就绪")

        threading.Thread(target=backup_thread, daemon=True).start()

    def _list_backups(self):
        """列出备份"""
        self._log("\n" + "="*50)
        self._log("备份列表:")
        self._log("="*50)

        backup_files = self.tool._get_backup_files()
        if not backup_files:
            self._log("没有找到备份文件")
            return

        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        for idx, backup in enumerate(backup_files, 1):
            size = self.tool._format_size(backup.stat().st_size)
            mtime = Path(backup).stat().st_mtime
            from datetime import datetime
            time_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            self._log(f"{idx}. {backup.name} ({size}) - {time_str}")

        self._log("="*50)

    def _verify_backup(self):
        """验证备份"""
        backup_files = self.tool._get_backup_files()
        if not backup_files:
            messagebox.showwarning("警告", "没有找到备份文件")
            return

        # 选择备份文件
        backup_names = [f.stem for f in backup_files]
        dialog = BackupSelectDialog(self.root, "选择要验证的备份", backup_names)
        if dialog.result:
            self._log(f"验证备份: {dialog.result}")
            is_valid = self.tool.verify(dialog.result)
            if is_valid:
                self._log("✅ 验证通过")
                messagebox.showinfo("成功", "备份验证通过!")
            else:
                self._log("❌ 验证失败")
                messagebox.showerror("错误", "备份验证失败!")

    def _restore_backup(self):
        """恢复备份"""
        backup_files = self.tool._get_backup_files()
        if not backup_files:
            messagebox.showwarning("警告", "没有找到备份文件")
            return

        # 选择备份文件
        backup_names = [f.stem for f in backup_files]
        dialog = BackupSelectDialog(self.root, "选择要恢复的备份", backup_names)
        if dialog.result:
            # 选择恢复路径
            restore_path = filedialog.askdirectory(title="选择恢复路径")
            if restore_path:
                self._log(f"恢复备份: {dialog.result} -> {restore_path}")
                success = self.tool.restore(dialog.result, restore_path)
                if success:
                    self._log("✅ 恢复完成")
                    messagebox.showinfo("成功", "备份恢复完成!")
                else:
                    self._log("❌ 恢复失败")
                    messagebox.showerror("错误", "备份恢复失败!")

    def _delete_backup(self):
        """删除备份"""
        backup_files = self.tool._get_backup_files()
        if not backup_files:
            messagebox.showwarning("警告", "没有找到备份文件")
            return

        # 选择备份文件
        backup_names = [f.stem for f in backup_files]
        dialog = BackupSelectDialog(self.root, "选择要删除的备份", backup_names)
        if dialog.result:
            if messagebox.askyesno("确认", f"确定要删除备份 {dialog.result} 吗?"):
                self._log(f"删除备份: {dialog.result}")
                success = self.tool.delete(dialog.result)
                if success:
                    self._log("✅ 删除完成")
                    messagebox.showinfo("成功", "备份已删除!")
                else:
                    self._log("❌ 删除失败")
                    messagebox.showerror("错误", "删除备份失败!")

    def run(self):
        """运行界面"""
        self.root.mainloop()


class BackupSelectDialog:
    """备份选择对话框"""

    def __init__(self, parent, title, items):
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 居中显示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

        # 列表框
        listbox_frame = ttk.Frame(self.dialog, padding="10")
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(listbox_frame, width=50, height=10)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.configure(yscrollcommand=scrollbar.set)

        for item in items:
            self.listbox.insert(tk.END, item)

        # 按钮
        btn_frame = ttk.Frame(self.dialog, padding="10")
        btn_frame.pack()

        ttk.Button(btn_frame, text="确定", command=self._on_ok).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="取消", command=self._on_cancel).pack(side=tk.LEFT)

    def _on_ok(self):
        selection = self.listbox.curselection()
        if selection:
            self.result = self.listbox.get(selection[0])
        self.dialog.destroy()

    def _on_cancel(self):
        self.dialog.destroy()


if __name__ == '__main__':
    app = BackupGUI()
    app.run()
