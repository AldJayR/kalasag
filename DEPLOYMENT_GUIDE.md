# 📦 KALASAG Deployment Guide

This guide explains how to package the KALASAG application into a standalone executable (`.exe`) file for Windows.

## Prerequisites

1.  **Python 3.10+** installed.
2.  **Virtual Environment** activated (recommended).

## 🚀 Quick Build

I have created a build script to automate the process.

1.  Open your terminal/command prompt.
2.  Navigate to the project folder.
3.  Run the build script:
    ```bash
    python build_exe.py
    ```

This script will:
*   Install `pyinstaller` if missing.
*   Package the application into a single file.
*   Place the result in the `dist/` folder.

## 📂 Output

*   **Executable**: `dist/KALASAG.exe`
*   **Database**: When you run the `.exe` for the first time, it will create `kalasag.db` in the **same folder** as the executable.
*   **Backups**: A `backups/` folder will also be created next to the executable.

## ⚠️ Important Notes

1.  **Antivirus**: Some antivirus software might flag the `.exe` as suspicious because it's not signed. This is normal for self-compiled Python apps. You can add an exclusion.
2.  **Database Persistence**: Keep the `kalasag.db` file safe. If you move the `.exe` to a new computer, copy the `.db` file with it if you want to keep your data.
3.  **Console Window**: The app is built in "Windowed" mode (no black console window). If you need to see error logs for debugging, edit `build_exe.py` and remove `--windowed`.

## 🛠 Manual Build Command

If you prefer to run PyInstaller manually:

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "KALASAG" --hidden-import babel.numbers --hidden-import PIL --hidden-import reportlab --hidden-import matplotlib --hidden-import sqlite3 main.py
```
