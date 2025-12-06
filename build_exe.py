import os
import subprocess
import sys
import shutil

def install_requirements():
    print("Checking/Installing PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build():
    print("Building KALASAG Executable...")
    
    # PyInstaller arguments
    args = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",  # No console window
        "--name", "KALASAG",
        "--clean",
        # Hidden imports often needed for these libraries
        "--hidden-import", "babel.numbers",
        "--hidden-import", "PIL",
        "--hidden-import", "reportlab",
        "--hidden-import", "matplotlib",
        "--hidden-import", "sqlite3",
        "main.py"
    ]
    
    try:
        subprocess.check_call(args)
        print("\n✅ Build Successful!")
        print(f"Executable can be found in: {os.path.join(os.getcwd(), 'dist', 'KALASAG.exe')}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build Failed: {e}")

if __name__ == "__main__":
    install_requirements()
    build()
