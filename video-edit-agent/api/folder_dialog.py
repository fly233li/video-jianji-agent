"""原生文件夹选择对话框 — tkinter 或 PowerShell 回退"""

from __future__ import annotations

import subprocess
import sys


TKINTER_SCRIPT = r"""
import tkinter as tk
from tkinter import filedialog
root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)
path = filedialog.askdirectory(title="{title}")
if path:
    print(path, end="")
root.destroy()
"""

FILE_DIALOG_SCRIPT = r"""
import tkinter as tk
from tkinter import filedialog
root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)
path = filedialog.askopenfilename(
    title="{title}",
    filetypes=[("3D LUT files", "*.cube"), ("All files", "*.*")],
)
if path:
    print(path, end="")
root.destroy()
"""

POWERSHELL_FOLDER_SCRIPT = """
Add-Type -AssemblyName System.Windows.Forms
$f = New-Object System.Windows.Forms.FolderBrowserDialog
$f.Description = '{title}'
$f.ShowNewFolderButton = $true
$r = $f.ShowDialog()
if ($r -eq [System.Windows.Forms.DialogResult]::OK) {{
    Write-Output $f.SelectedPath
}}
"""

POWERSHELL_FILE_SCRIPT = """
Add-Type -AssemblyName System.Windows.Forms
$f = New-Object System.Windows.Forms.OpenFileDialog
$f.Title = '{title}'
$f.Filter = '{filter}'
$f.CheckFileExists = $true
$r = $f.ShowDialog()
if ($r -eq [System.Windows.Forms.DialogResult]::OK) {{
    Write-Output $f.FileName
}}
"""


def _find_system_python() -> str | None:
    """在打包后的应用中寻找系统 Python"""
    candidates = [
        # Python 3.13
        r"C:\Program Files\Python313\python.exe",
        r"C:\Users\q\AppData\Local\Programs\Python\Python313\python.exe",
        # Python 3.12
        r"C:\Program Files\Python312\python.exe",
        r"C:\Users\q\AppData\Local\Programs\Python\Python312\python.exe",
        # Python 3.11
        r"C:\Program Files\Python311\python.exe",
        r"C:\Users\q\AppData\Local\Programs\Python\Python311\python.exe",
        # Python Launcher
        r"C:\Windows\py.exe",
    ]
    for py in candidates:
        try:
            r = subprocess.run([py, "--version"], capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and "Python" in r.stdout:
                return py
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    # 尝试 PATH 中的 python
    try:
        r = subprocess.run(["python", "--version"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and "Python" in r.stdout:
            return "python"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _run_via_powershell(script: str) -> str | None:
    """通过 PowerShell 运行对话框"""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout.strip()
        return output if output else None
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        print(f"  [WARNING] PowerShell 对话框失败: {e}")
        return None


def show_folder_dialog(title: str = "请选择文件夹") -> str | None:
    """弹出系统原生文件夹选择对话框"""
    python_exe = _find_system_python() if getattr(sys, "frozen", False) else sys.executable

    if python_exe:
        script = TKINTER_SCRIPT.format(title=title)
        try:
            result = subprocess.run(
                [python_exe, "-c", script],
                capture_output=True, text=True, timeout=120,
            )
            output = result.stdout.strip()
            if output:
                return output
        except Exception:
            pass

    # 回退到 PowerShell
    return _run_via_powershell(POWERSHELL_FOLDER_SCRIPT.format(title=title))


def show_file_dialog(title: str = "请选择 LUT 文件") -> str | None:
    """弹出系统原生文件选择对话框（.cube 文件）"""
    python_exe = _find_system_python() if getattr(sys, "frozen", False) else sys.executable

    if python_exe:
        script = FILE_DIALOG_SCRIPT.format(title=title)
        try:
            result = subprocess.run(
                [python_exe, "-c", script],
                capture_output=True, text=True, timeout=120,
            )
            output = result.stdout.strip()
            if output:
                return output
        except Exception:
            pass

    # 回退到 PowerShell
    return _run_via_powershell(
        POWERSHELL_FILE_SCRIPT.format(
            title=title,
            filter="LUT 文件 (*.cube)|*.cube|所有文件 (*.*)|*.*",
        )
    )
