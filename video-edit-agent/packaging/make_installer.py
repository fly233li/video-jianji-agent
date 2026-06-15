"""
创建 Windows 安装程序
1. 扫描 dist/视频剪辑助手/ 目录
2. 生成 IExpress SED 文件
3. 调用 IExpress 生成安装包
"""
import os
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT / "dist" / "视频剪辑助手"
OUTPUT = PROJECT / "dist" / "视频剪辑助手_安装程序.exe"
IEXPRESS = r"C:\Windows\System32\iexpress.exe"


def build_sed() -> str:
    """生成 IExpress SED 文件内容"""
    # 收集所有文件（相对于 DIST_DIR）
    files = []
    for root, dirs, fnames in os.walk(str(DIST_DIR)):
        for fname in fnames:
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, str(DIST_DIR))
            files.append((full, rel))

    sed_lines = [
        "[Version]",
        "Class=IEXPRESS",
        "SEDVersion=3",
        "",
        "[Options]",
        f"PackagePurpose=InstallApp",
        "ShowInstallProgramWindow=0",
        "HideExtractAnimation=1",
        "UseLongFileName=1",
        "InsideCompressed=1",
        "CAB_FixedSize=0",
        "CAB_MaxSizeInBytes=0",
        "",
        "[SourceFiles]",
        "SourceFiles0=Source",
        "[SourceFiles0]",
    ]

    for i, (full, rel) in enumerate(files):
        sed_lines.append(f"%FILE{i}%={full}")

    sed_lines.extend([
        "",
        "[DestinationDir]",
        "DestinationDir0=",  # empty = use TEMP, then run install command
        "",
        "[Strings]",
        "AppName=视频剪辑助手",
        "AppURL=",
        "AppVer=2.0.0",
        "PostInstallCmd=<None>",
        "InstallPrompt=是否安装视频剪辑助手到当前目录？",
        "Untitled=视频剪辑助手 安装程序",
        "DisplayLicense=",
    ])

    # Generate DisplayProgress menu items
    for i, (full, rel) in enumerate(files):
        sed_lines.append(f"DisplayProgress{i}%={rel}")

    return "\r\n".join(sed_lines)


def main():
    if not DIST_DIR.exists():
        print(f"[ERROR] 未找到构建目录: {DIST_DIR}")
        print("请先运行 PyInstaller 打包")
        return 1

    if not IEXPRESS or not os.path.exists(IEXPRESS):
        print("[WARNING] IExpress 不可用，跳过安装程序创建")
        return 1

    print(f"扫描目录: {DIST_DIR}")
    sed_content = build_sed()

    sed_path = PROJECT / "packaging" / "installer.sed"
    sed_path.write_text(sed_content, encoding="utf-8")

    print(f"SED 文件已生成: {sed_path}")
    print(f"正在调用 IExpress...")

    try:
        result = subprocess.run(
            [IEXPRESS, "/N", "/Q", str(sed_path)],
            capture_output=True, text=True, timeout=120,
        )
        print(f"IExpress 输出: {result.stdout}")
        if result.stderr:
            print(f"stderr: {result.stderr}")

        if OUTPUT.exists():
            size_mb = OUTPUT.stat().st_size / (1024 * 1024)
            print(f"\n[OK] 安装程序创建成功: {OUTPUT} ({size_mb:.1f} MB)")
            return 0
        else:
            print("[WARNING] IExpress 可能未生成安装程序，请检查")
            return 1

    except Exception as e:
        print(f"[WARNING] IExpress 调用失败: {e}")
        print("可手动使用 iexpress.exe 创建安装程序")
        return 1


if __name__ == "__main__":
    sys.exit(main())
