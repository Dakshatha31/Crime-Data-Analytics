"""
Web Server Launcher.
Starts the FastAPI application and serves the Light Theme UI at http://127.0.0.1:8000
"""
import sys
import uvicorn
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_all_pipelines import run_all


def main():
    print("=" * 70)
    print("  STARTING CRIME DATA ANALYTICS WEB PLATFORM")
    print("=" * 70)
    print("[*] Checking data pipelines and ensuring HDFS warehouse...")
    try:
        run_all()
    except Exception as e:
        print(f"[!] Pipeline notice: {e}")

    print("\n[+] Web Application Online:")
    print("    URL     : http://127.0.0.1:8000")
    print("    API Docs: http://127.0.0.1:8000/docs")
    print("    Theme   : Clean Light Theme")
    print("    Map     : Interactive Landing Page Map & Hotspots")
    print("=" * 70 + "\n")

    uvicorn.run("web.server:app", host="127.0.0.1", port=8000, log_level="info", reload=False)


if __name__ == "__main__":
    main()
